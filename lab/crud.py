"""Equivalent, intentionally segregated order CRUD for the live demonstration."""
from contextlib import ExitStack
from datetime import datetime, timezone
from uuid import uuid4

from .db import connect_mongo, connect_pg, normalize

DEMO_NAMESPACE = 'bd_lab_crud_demo'

class PostgresOrders:
    def __init__(self, connection):
        self.connection = connection
        with connection.transaction(), connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(481803176)")
            cur.execute("""
              CREATE SCHEMA IF NOT EXISTS bd_lab_crud_demo;
              CREATE TABLE IF NOT EXISTS bd_lab_crud_demo.orders (
                  id uuid PRIMARY KEY,
                  customer_id integer NOT NULL,
                  created_at timestamptz NOT NULL,
                  status text NOT NULL CHECK (status IN ('criado', 'concluido')),
                  total_cents integer NOT NULL CHECK (total_cents >= 0)
              );
              CREATE TABLE IF NOT EXISTS bd_lab_crud_demo.items (
                  order_id uuid NOT NULL REFERENCES bd_lab_crud_demo.orders(id) ON DELETE CASCADE,
                  position integer NOT NULL, product_id integer NOT NULL,
                  product_name text NOT NULL, quantity integer NOT NULL CHECK (quantity > 0),
                  unit_cents integer NOT NULL CHECK (unit_cents >= 0),
                  PRIMARY KEY (order_id, position)
              );
            """)

    def create(self, order):
        with self.connection.transaction(), self.connection.cursor() as cur:
            cur.execute("""
              INSERT INTO bd_lab_crud_demo.orders (id, customer_id, created_at, status, total_cents)
              VALUES (%(id)s, %(customer_id)s, %(created_at)s, %(status)s, %(total_cents)s)
            """, order)
            cur.executemany("""
              INSERT INTO bd_lab_crud_demo.items (order_id, position, product_id, product_name, quantity, unit_cents)
              VALUES (%(order_id)s, %(position)s, %(product_id)s, %(product_name)s, %(quantity)s, %(unit_cents)s)
            """, [dict(item, order_id=order['id']) for item in order['items']])

    def read(self, oid):
        with self.connection.transaction(), self.connection.cursor() as cur:
            cur.execute("""
              SELECT o.id::text AS id, o.customer_id, o.created_at, o.status, o.total_cents,
                jsonb_agg(jsonb_build_object(
                  'position', i.position, 'product_id', i.product_id, 'product_name', i.product_name,
                  'quantity', i.quantity, 'unit_cents', i.unit_cents
                ) ORDER BY i.position) AS items
              FROM bd_lab_crud_demo.orders o
              JOIN bd_lab_crud_demo.items i ON i.order_id=o.id
              WHERE o.id=%s GROUP BY o.id
            """, (oid,))
            return normalize(cur.fetchone())

    def update(self, order):
        with self.connection.transaction(), self.connection.cursor() as cur:
            cur.execute("""
              UPDATE bd_lab_crud_demo.orders SET status=%(status)s, total_cents=%(total_cents)s
              WHERE id=%(id)s
            """, order)
            if cur.rowcount != 1:
                raise RuntimeError('Pedido de demonstração não encontrado no PostgreSQL.')
            for item in order['items']:
                cur.execute("""
                  UPDATE bd_lab_crud_demo.items SET quantity=%s WHERE order_id=%s AND position=%s
                """, (item['quantity'], order['id'], item['position']))
                if cur.rowcount != 1:
                    raise RuntimeError('Item de demonstração não encontrado no PostgreSQL.')

    def delete(self, oid):
        with self.connection.transaction(), self.connection.cursor() as cur:
            cur.execute("DELETE FROM bd_lab_crud_demo.orders WHERE id=%s", (oid,))
            return cur.rowcount

class MongoOrders:
    def __init__(self, client):
        self.collection = client[DEMO_NAMESPACE]['orders']

    def create(self, order):
        self.collection.insert_one(dict(_id=order['id'], **{k:v for k,v in order.items() if k != 'id'}))

    def read(self, oid):
        doc = self.collection.find_one({'_id':oid}, max_time_ms=5000)
        if doc is not None:
            doc['id'] = doc.pop('_id')
        return normalize(doc)

    def update(self, order):
        result = self.collection.update_one({'_id':order['id']}, {'$set': {
            'status':order['status'], 'total_cents':order['total_cents'], 'items':order['items'],
        }})
        if result.matched_count != 1:
            raise RuntimeError('Pedido de demonstração não encontrado no MongoDB.')

    def delete(self, oid):
        return self.collection.delete_one({'_id':oid}).deleted_count

def with_total(order, items):
    return {**order, 'items':items, 'total_cents':sum(i['unit_cents'] * i['quantity'] for i in items)}

def run_scenario(pg, mongo):
    """Execute and verify the exact same lifecycle, with no arbitrary input IDs."""
    oid = str(uuid4())
    created_at = datetime.now(timezone.utc).replace(microsecond=0)
    items = [
        {'position':0, 'product_id':101, 'product_name':'Caneca de demonstração', 'quantity':2, 'unit_cents':3150},
        {'position':1, 'product_id':102, 'product_name':'Caderno de demonstração', 'quantity':1, 'unit_cents':4150},
    ]
    initial = with_total({'id':oid, 'customer_id':1, 'created_at':created_at, 'status':'criado'}, items)
    changed = with_total({**initial, 'status':'concluido'}, [{**items[0], 'quantity':3}, items[1]])
    backends = {'postgres':pg, 'mongo':mongo}
    active = {}
    try:
        for name, backend in backends.items():
            backend.create(initial)
            active[name] = backend
        def read_equivalent(expected, phase):
            rows = {name:normalize(b.read(oid)) for name,b in backends.items()}
            if any(row != normalize(expected) for row in rows.values()):
                raise RuntimeError(f'Resultados divergentes na etapa {phase}.')
            return rows['postgres']

        before = read_equivalent(initial, 'leitura')
        for backend in backends.values():
            backend.update(changed)
        after = read_equivalent(changed, 'atualização')
        deleted = {}
        for name, backend in backends.items():
            deleted[name] = backend.delete(oid)
            del active[name]
        missing = {name:backend.read(oid) for name,backend in backends.items()}
        if any(count != 1 for count in deleted.values()) or any(row is not None for row in missing.values()):
            raise RuntimeError('Exclusão da demonstração não confirmada nos dois bancos.')
        return {
            'status':'ok', 'demo_id':oid, 'namespace':DEMO_NAMESPACE,
            'create':{'postgres':1,'mongo':1}, 'read':before, 'update':after,
            'delete':deleted, 'after_delete':missing,
        }
    except Exception as original:
        for name, backend in active.items():
            try:
                backend.delete(oid)
            except Exception as cleanup:
                original.add_note(f'Não foi possível limpar apenas o UUID de teste {oid} em {name}: {cleanup}')
        raise

def crud_demo():
    with ExitStack() as stack:
        pg = stack.enter_context(connect_pg())
        mongo = stack.enter_context(connect_mongo())
        mongo.admin.command('ping')
        return run_scenario(PostgresOrders(pg), MongoOrders(mongo))
