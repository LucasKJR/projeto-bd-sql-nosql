import os,json,time
from datetime import datetime,timezone
SQL={
"order":"""SELECT o.id,o.customer_id,o.created_at,o.status,o.total_cents,
jsonb_agg(jsonb_build_object('position',i.position,'product_id',i.product_id,'product_name',i.product_name,'quantity',i.quantity,'unit_cents',i.unit_cents) ORDER BY i.position) AS items
FROM orders o JOIN items i ON i.order_id=o.id WHERE o.id=%s GROUP BY o.id""",
"daily":"""SELECT to_char(created_at AT TIME ZONE 'UTC','YYYY-MM-DD') AS day,count(*) AS orders,sum(total_cents)::bigint AS total_cents FROM orders
WHERE status='concluido' AND created_at>=%s AND created_at<%s GROUP BY day ORDER BY day""",
"top":"""SELECT i.product_id,sum(i.quantity)::bigint AS quantity,sum(i.quantity::bigint*i.unit_cents)::bigint AS total_cents
FROM orders o JOIN items i ON o.id=i.order_id WHERE o.status='concluido' AND o.created_at>=%s AND o.created_at<%s
GROUP BY i.product_id ORDER BY quantity DESC,total_cents DESC,product_id ASC LIMIT 10"""
}
SQL["batch"]=SQL["order"].replace("WHERE o.id=%s GROUP BY o.id","WHERE o.id>=%s AND o.id<%s GROUP BY o.id ORDER BY o.id")
SCHEMA="""CREATE TABLE customers(id bigint PRIMARY KEY,name text NOT NULL);
CREATE TABLE products(id bigint PRIMARY KEY,sku text UNIQUE NOT NULL,name text NOT NULL);
CREATE TABLE orders(id bigint PRIMARY KEY,customer_id bigint REFERENCES customers,created_at timestamptz NOT NULL,status text NOT NULL CHECK(status IN ('criado','concluido','cancelado')),total_cents bigint NOT NULL);
CREATE TABLE items(order_id bigint REFERENCES orders,position integer,product_id bigint REFERENCES products,product_name text NOT NULL,quantity integer NOT NULL CHECK(quantity>0),unit_cents bigint NOT NULL CHECK(unit_cents>=0),PRIMARY KEY(order_id,position));
CREATE INDEX orders_status_date ON orders(status,created_at);
CREATE INDEX items_product ON items(product_id);"""
def mongo_pipeline(kind,a,b,oid):
    if kind=="order":
        return [{"$match":{"_id":oid}},{"$project":{"_id":0,"id":"$_id","customer_id":1,"created_at":1,"status":1,"total_cents":1,"items":1}}]
    match={"$match":{"status":"concluido","created_at":{"$gte":a,"$lt":b}}}
    if kind=="daily":
        return [match,{"$group":{"_id":{"$dateToString":{"format":"%Y-%m-%d","date":"$created_at","timezone":"UTC"}},"orders":{"$sum":1},"total_cents":{"$sum":"$total_cents"}}},{"$sort":{"_id":1}},{"$project":{"_id":0,"day":"$_id","orders":1,"total_cents":1}}]
    if kind=="top":
        return [match,{"$unwind":"$items"},{"$group":{"_id":"$items.product_id","quantity":{"$sum":"$items.quantity"},"total_cents":{"$sum":{"$multiply":["$items.quantity","$items.unit_cents"]}}}},{"$sort":{"quantity":-1,"total_cents":-1,"_id":1}},{"$limit":10},{"$project":{"_id":0,"product_id":"$_id","quantity":1,"total_cents":1}}]
    raise ValueError("Consulta desconhecida")
def connect_pg():
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(os.getenv("PG_DSN","postgresql://lab:local-lab-only@127.0.0.1:55432/bd_lab"),row_factory=dict_row,connect_timeout=5)
def connect_mongo():
    from pymongo import MongoClient
    return MongoClient(os.getenv("MONGO_URI","mongodb://127.0.0.1:57017"),serverSelectionTimeoutMS=5000,tz_aware=True)
def normalize(value):
    if isinstance(value,datetime): return value.astimezone(timezone.utc).isoformat()
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
    if isinstance(value,list): return [normalize(v) for v in value]
    return value
def mongo_order_rows(collection,oid,size=1):
    cursor=collection.find({'_id':oid} if size==1 else {'_id':{'$gte':oid,'$lt':oid+size}})
    rows=list(cursor if size==1 else cursor.sort('_id',1))
    for row in rows: row['id']=row.pop('_id')
    return rows

def run(source,kind,a,b,oid,connection=None):
    if source not in ("postgres","mongo") or kind not in SQL: raise ValueError("Fonte/consulta inválida")
    own=connection is None
    c=connection or (connect_pg() if source=="postgres" else connect_mongo())
    try:
        if own and source=="mongo": c.admin.command("ping")
        start=time.perf_counter_ns()
        if source=="postgres":
            with c.cursor() as cur:
                cur.execute(SQL[kind],(oid,) if kind=="order" else ((oid,oid+100) if kind=='batch' else (a,b)))
                rows=cur.fetchall()
        elif kind in ('order','batch'): rows=mongo_order_rows(c.bd_lab.orders,oid,100 if kind=='batch' else 1)
        else: rows=list(c.bd_lab.orders.aggregate(mongo_pipeline(kind,a,b,oid),allowDiskUse=True))
        rows=normalize(rows)
        # Both paths include complete materialization and the same JSON serialization.
        json.dumps(rows,sort_keys=True)
        elapsed=(time.perf_counter_ns()-start)/1e6
        return dict(rows=rows,elapsed_ms=elapsed,source=source,query=kind)
    finally:
        if own: c.close()
