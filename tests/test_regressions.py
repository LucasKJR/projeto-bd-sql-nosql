import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from lab.workflow import benchmark
from lab.db import run
from lab.core import validate_filters
class Regressions(unittest.TestCase):
 def test_benchmark_refuses_old_results(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'benchmark.json').write_text('{}')
   with self.assertRaises(FileExistsError): benchmark(d)
 def test_mongo_connect_precedes_timer(self):
  events=[]
  class Fake:
   def __getattr__(self,k): return self
   def command(self,*args): events.append('ping')
   def aggregate(self,*args,**kw): events.append('query');return []
   def find(self,*args,**kw): events.append('query');return []
   def close(self): pass
  def tick(): events.append('timer');return 1
  a,b,oid=validate_filters('2025-01-01','2026-01-01',1)
  with patch('lab.db.connect_mongo',return_value=Fake()),patch('lab.db.time.perf_counter_ns',side_effect=tick):
   run('mongo','order',a,b,oid)
  self.assertEqual(events[:2],['ping','timer'])
