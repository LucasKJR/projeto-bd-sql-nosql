import unittest
from lab.browser import parse_browser
class BrowserTests(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(parse_browser('/api/documents'), ('orders', 0, False))
    def test_collections_and_id(self):
        for name in ('orders','customers','products'):
            self.assertEqual(parse_browser('/api/documents?collection='+name+'&id=123'), (name,123,True))
    def test_rejects_unsafe_inputs(self):
        for query in ('collection=admin','id=-1','id=0','after=2147483648','id=1&after=0','filter=x','id=1.5'):
            with self.assertRaises(ValueError): parse_browser('/api/documents?'+query)
