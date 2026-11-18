import unittest
from lab.db import mongo_order_rows
class Direct(unittest.TestCase):
 def test_rename_id_and_preserve_items(self):
  class Collection:
   def find(self,query):
    assert query=={'_id':17}
    return [{'_id':17,'items':[{'position':0}]}]
  self.assertEqual(mongo_order_rows(Collection(),17),[{'id':17,'items':[{'position':0}]}])
