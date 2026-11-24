import json
import unittest
from urllib.parse import urlencode
from lab.explorer import parse, sql_query, mongo_query

def args(**kwargs):
    return '/api/explore?' + urlencode(kwargs)

class ExplorerTests(unittest.TestCase):
    def test_composite_cursor_and_bound_sql(self):
        q=parse(args(source='postgres',entity='items',limit=10,after='[100,2]',filters=json.dumps([['product_name','eq',"Produto d'oeste"],['quantity','gte','3']])))
        stmt,values,preview=sql_query(q)
        self.assertIn('FROM "public"."items"',stmt)
        self.assertIn('("order_id", "position") > (%s, %s)',stmt)
        self.assertNotIn("d'oeste",stmt)
        self.assertEqual(values,["Produto d'oeste",3,100,2,11])
        self.assertIn("d''oeste",preview)
    def test_mongo_multi_filters_remain_inside_and(self):
        q=parse(args(source='mongo',entity='orders',filters=json.dumps([['status','eq','concluido'],['items.product_id','eq',31],['created_at','gte','2025-01-01']]),after='[7]'))
        match,preview=mongo_query(q)
        self.assertIn({'items.product_id':31},match['$and'])
        self.assertIn({'_id':{'$gt':7}}, match['$and'])
        self.assertIn('ISODate(',preview)
    def test_allowlist_and_limits(self):
        for request in [args(source='postgres',entity='pg_user'),args(source='mongo',entity='items'),args(entity='orders',limit=1000),args(entity='orders',after='[0,1]'),args(filters=json.dumps([['status','$where','return true']])),args(filters=json.dumps([['id','eq',True]])),args(filters=json.dumps([['bogus','eq','123']]))]:
            with self.assertRaises(ValueError): parse(request)

class ExplorerProjectionTests(unittest.TestCase):
    def test_postgres_uses_projection_but_keeps_cursor_internally(self):
        q=parse(args(source='postgres',entity='items',select='["product_name"]'))
        stmt,values,_=sql_query(q)
        self.assertTrue(stmt.startswith('SELECT "product_name", "order_id", "position"\n'))
        self.assertNotIn('unit_cents',stmt)
        self.assertEqual(q[-1],('product_name',))

    def test_mongo_projection_is_safe_for_embedded_and_id(self):
        from lab.explorer import mongo_projection
        q=parse(args(source='mongo',entity='orders',select='["items","status"]'))
        self.assertEqual(mongo_projection(q),{'items':1,'status':1,'_id':1})
        self.assertEqual(q[-1],('items','status'))

    def test_projection_rejects_disallowed_and_empty(self):
        for selected in ('[]','["password"]','["id","id"]','["$where"]','[{}]'):
            with self.assertRaises(ValueError):
                parse(args(source='postgres',entity='orders',select=selected))
