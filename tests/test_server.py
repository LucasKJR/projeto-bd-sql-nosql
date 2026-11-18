import unittest
from lab.server import parse_request
class Server(unittest.TestCase):
    def test_parse_and_reject(self):
        source,kind,a,b,oid=parse_request('/api/query?source=mongo&query=order&order_id=3')
        self.assertEqual((source,kind,oid),('mongo','order',3))
        with self.assertRaises(ValueError): parse_request('/api/query?source=bad')
