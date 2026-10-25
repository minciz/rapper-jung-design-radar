import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from select_inbox import eligible_paths

KST = timezone(timedelta(hours=9))
class InboxSelectionTests(unittest.TestCase):
    def sample(self, title="Valid"):
        date=datetime.now(KST).date().isoformat()
        return {"briefing_date":date,"topic":"test","test_only":False,"references":[{"title":title+str(i),"original_page_url":"https://example.org/work/"+str(i),"verification":{"source_match":True,"image_access":False}} for i in range(12)],"trends":[{"title":str(i),"summary":"summary","checked_date":date,"source_urls":["https://example.org/news"]} for i in range(3)]}
    def test_excludes_test_only_and_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"test.json").write_text(json.dumps({**self.sample(),"test_only":True}))
            (root/"invalid.json").write_text("{}")
            (root/"real.json").write_text(json.dumps(self.sample()))
            self.assertEqual([p.name for p in eligible_paths(root,[])],["real.json"])
    def test_excludes_insufficient_reference_count(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            raw=self.sample();raw["references"]=raw["references"][:11]
            (root/"short.json").write_text(json.dumps(raw))
            self.assertEqual(eligible_paths(root,[]),[])
    def test_excludes_missing_explicit_production_flag(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            raw=self.sample();raw.pop("test_only")
            (root/"missing_flag.json").write_text(json.dumps(raw))
            self.assertEqual(eligible_paths(root,[]),[])
    def test_excludes_published_day(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            raw=self.sample()
            (root/"real.json").write_text(json.dumps(raw))
            self.assertEqual(eligible_paths(root,[{"day":raw["briefing_date"]}]),[])
if __name__=="__main__":
    unittest.main()
