import unittest
from lab.db import mongo_pipeline, SQL
from lab.core import validate_filters
class Queries(unittest.TestCase):
    def test_pipeline_filters_and_tie(self):
        a,b,_=validate_filters('2025-01-01','2026-01-01',1)
        p=mongo_pipeline('top',a,b,1)
        self.assertEqual(p[0]['$match']['status'],'concluido')
        self.assertEqual(p[-3]['$sort'],{'quantity':-1,'total_cents':-1,'_id':1})
        self.assertIn('$lt',p[0]['$match']['created_at'])
    def test_sql_parameterized(self):
        self.assertIn('%s',SQL['order'])
        self.assertIn("status='concluido'",SQL['daily'])
        self.assertIn('product_id ASC',SQL['top'])
