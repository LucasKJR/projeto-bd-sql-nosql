import tempfile,unittest,json
from pathlib import Path
from lab.workflow import generate
class Workflow(unittest.TestCase):
    def test_generate_manifest_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data'
            m=generate(p,20,42)
            self.assertEqual(m['orders'],20)
            self.assertTrue(m['items']>=20)
            self.assertEqual(len((p/'orders.jsonl').read_text().splitlines()),20)
            self.assertEqual(len(m['sha256']),64)
            with self.assertRaises(FileExistsError): generate(p,20,42)
