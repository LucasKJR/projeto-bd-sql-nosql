import copy
import unittest
from unittest.mock import patch

from lab.crud import run_scenario

class MemoryStore:
    def __init__(self, database):
        self.database = database
        self.records = {}
    def create(self, order):
        self.records[order['id']] = copy.deepcopy(order)
    def read(self, oid):
        return copy.deepcopy(self.records.get(oid))
    def update(self, order):
        self.records[order['id']] = copy.deepcopy(order)
    def delete(self, oid):
        return int(self.records.pop(oid, None) is not None)

class CrudTests(unittest.TestCase):
    def setUp(self):
        self.pg, self.mongo = MemoryStore('pg'), MemoryStore('mongo')
        for backend in (self.pg, self.mongo):
            backend.records['outside'] = {'id':'outside'}

    def test_equivalent_lifecycle_preserves_existing_records(self):
        result = run_scenario(self.pg, self.mongo)
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['read']['total_cents'],10450)
        self.assertEqual(result['update']['total_cents'],13600)
        self.assertEqual(result['update']['status'],'concluido')
        self.assertEqual(result['update']['items'][0]['quantity'],3)
        self.assertEqual(result['delete'],{'postgres':1,'mongo':1})
        self.assertEqual(result['after_delete'],{'postgres':None,'mongo':None})
        for b in (self.pg,self.mongo):
            self.assertEqual(b.records, {'outside': {'id':'outside'}})

    def test_different_results_fail_and_clean_only_generated_id(self):
        base_read = self.mongo.read
        def corrupt(oid):
            row = base_read(oid)
            if row:
                row['total_cents'] += 1
            return row
        with patch.object(self.mongo,'read',side_effect=corrupt):
            with self.assertRaisesRegex(RuntimeError, 'divergentes'):
                run_scenario(self.pg, self.mongo)
        for b in (self.pg,self.mongo):
            self.assertEqual(b.records, {'outside': {'id':'outside'}})
