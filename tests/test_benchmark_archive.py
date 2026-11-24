import unittest
from lab.benchmark_archive import history

class BenchmarkArchiveTests(unittest.TestCase):
    def test_history_reconciles_archived_variant_medians_and_counts(self):
        data=history()
        self.assertEqual(data['run_date'],'2026-11-17')
        self.assertEqual([r['code'] for r in data['rows']],['Q1','Q2','Q3','Q4'])
        self.assertEqual([r['samples'] for r in data['rows']],[1000,10,10,300])
        self.assertEqual([r['winner'] for r in data['rows']],['PostgreSQL']*3+['MongoDB'])
        self.assertAlmostEqual(data['rows'][0]['postgres_ms'],1.059396)
        self.assertAlmostEqual(data['rows'][2]['mongo_ms'],8953.051729)
        self.assertAlmostEqual(data['rows'][3]['lower_pct'],41.88,places=1)
