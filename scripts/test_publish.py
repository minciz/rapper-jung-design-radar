import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from normalize import normalize
from publish import publish
KST=timezone(timedelta(hours=9))
class TestRadar(unittest.TestCase):
    def sample(self):
        date=datetime.now(KST).date().isoformat()
        return {'briefing_date':date,'topic':'검증용 아카이브','references':[{'title':f'작품 {i}','original_page_url':f'https://example.org/art/{i}','image_url':f'https://example.org/img/{i}.jpg','verification':{'source_match':True,'image_access':True}} for i in range(15)],'trends':[{'title':f'동향 {i}','summary':'검증용','checked_date':date,'source_urls':[f'https://example.org/news/{i}']} for i in range(3)]}
    def test_normalize(self):
        result=normalize(self.sample())
        self.assertEqual(len(result['references']),15)
        self.assertEqual(len(result['signals']),3)
        self.assertEqual(result['references'][0]['source_url'],'https://example.org/art/0')
    def test_reject_missing_reference(self):
        raw=self.sample();raw['references'].pop()
        with self.assertRaisesRegex(ValueError,'15'): normalize(raw)
    def test_reject_unverified_source(self):
        raw=self.sample();raw['references'][0]['verification']['source_match']=False
        with self.assertRaisesRegex(ValueError,'verified original'): normalize(raw)
    def test_hide_unverified_image(self):
        raw=self.sample();raw['references'][0]['verification']['image_access']=False
        self.assertIsNone(normalize(raw)['references'][0]['image_url'])
    def test_reject_missing_trend_source(self):
        raw=self.sample();raw['trends'][0]['source_urls']=[]
        with self.assertRaisesRegex(ValueError,'source required'): normalize(raw)
    def test_reject_future(self):
        raw=self.sample();raw['briefing_date']='2099-01-01'
        with self.assertRaisesRegex(ValueError,'Future'): normalize(raw)
    def test_publish_roundtrip_and_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            data=Path(td)/'entries.json';history=Path(td)/'history.json'
            entry=normalize(self.sample())
            publish(entry,data,history)
            self.assertEqual(len(json.loads(data.read_text(encoding='utf-8'))),1)
            self.assertEqual(len(json.loads(history.read_text(encoding='utf-8'))),1)
            with self.assertRaisesRegex(ValueError,'Already published'): publish(entry,data,history)
if __name__=='__main__': unittest.main()
