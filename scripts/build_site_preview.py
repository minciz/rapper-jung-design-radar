"""Generate a site-schema preview without publishing or fabricating editorial analysis."""
import json,sys
from datetime import datetime, timezone, timedelta
KST=timezone(timedelta(hours=9))
with open(sys.argv[1],encoding="utf-8") as f: queue=json.load(f)
items=queue["items"]
preview={
 "test_only":True,
 "publish_blocked":True,
 "block_reasons":["visual_review_missing","editorial_theme_unapproved","trend_signals_unverified"],
 "schema_version":"1.0",
 "date":datetime.now(KST).date().isoformat()+"T12:00:00+09:00",
 "theme":None,
 "references":[{
  "title":x["title"],"creator":None,"year":None,
  "image_url":x.get("image_url"),"source_url":x["source_url"],
  "reason":None,"visual_features":None,
  "verification_reason":"시각 검토 및 작품 일치 검증 대기",
  "verification":{"source_match":False,"image_access":False,"visually_reviewed":False},
  "usage_rights_status":"unverified"
 } for x in items],
 "signals":[],
 "actual_count":len(items),
 "target_count":15
}
with open("free_source_site_preview.json","w",encoding="utf-8") as f:json.dump(preview,f,ensure_ascii=False,indent=2)
print("Site preview created; publishing explicitly blocked:",", ".join(preview["block_reasons"]))
