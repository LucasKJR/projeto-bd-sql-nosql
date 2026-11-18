import unittest
from lab.core import orders, validate_filters, summarize

class CoreTests(unittest.TestCase):
    def test_reproducible_and_valid(self):
        a=list(orders(100,42)); self.assertEqual(a,list(orders(100,42)))
        self.assertEqual(len({o['id'] for o in a}),100)
        for o in a:
            self.assertTrue(1<=len(o['items'])<=10)
            self.assertEqual(o['total_cents'],sum(x['quantity']*x['unit_cents'] for x in o['items']))
    def test_filters(self):
        self.assertEqual(validate_filters('2025-01-01','2026-01-01',1)[2],1)
        for args in [('bad','2026-01-01',1),('2026-01-01','2025-01-01',1),('2025-01-01','2026-01-01',0)]:
            with self.assertRaises(ValueError): validate_filters(*args)
    def test_statistics(self):
        self.assertEqual(summarize([1,2,3,4])['median_ms'],2.5)
        with self.assertRaises(ValueError): summarize([])

if __name__=='__main__': unittest.main()
