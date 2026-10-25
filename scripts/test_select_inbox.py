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
        return {"briefing_date":date,"topic":"test","references":[{"title":title,"original_page_url":"https://example.org/work","verification":{"source_match":True,"image_access":False}}],"trends":[{"title":str(i),"summary":"summary","checked_date":date,"source_urls":["https://example.org/news"]} for i in range(3)]}
    def test_excludes_test_only_and_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"test.json").write_text(json.dumps({**self.sample(),"test_only":True}))
            (root/"invalid.json").write_text("{}")
            (root/"real.json").write_text(json.dumps(self.sample()))
            self.assertEqual([p.name for p in eligible_paths(root,[])],["real.json"])
    def test_excludes_published_day(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            raw=self.sample()
            (root/"real.json").write_text(json.dumps(raw))
            self.assertEqual(eligible_paths(root,[{"day":raw["briefing_date"]}]),[])
if __name__=="__main__":
    unittest.main()
