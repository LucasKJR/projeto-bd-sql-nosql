import unittest
from lab.db import SQL,mongo_order_rows
class Batch(unittest.TestCase):
 def test_sql_batch_is_ordered_and_indexable(self):
  self.assertIn('o.id>=%s AND o.id<%s',SQL['batch'])
  self.assertIn('ORDER BY o.id',SQL['batch'])
 def test_mongo_batch_bounds_and_order(self):
  class Cursor(list):
   def sort(self,key,direction):
    self.asserted=(key,direction); return self
  class Collection:
   def find(self,query):
    assert query=={'_id':{'$gte':17,'$lt':117}}
    return Cursor([{'_id':17,'items':[]}])
  self.assertEqual(mongo_order_rows(Collection(),17,100),[{'id':17,'items':[]}])
