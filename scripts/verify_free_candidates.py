"""Test-only candidate URL and image metadata checks. No publication."""
import json,sys,urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse
class Parser(HTMLParser):
 def __init__(self): super().__init__();self.meta={}
 def handle_starttag(self,tag,attrs):
  if tag=="meta":
   d=dict(attrs);key=d.get("property") or d.get("name")
   if key and d.get("content"):self.meta[key.lower()]=d["content"]
def check(item):
 result=dict(item);result["verification"]={"source_match":False,"image_access":False,"visually_reviewed":False};result["eligible_for_publish"]=False
 try:
  req=urllib.request.Request(item["source_url"],headers={"User-Agent":"Mozilla/5.0"})
  with urllib.request.urlopen(req,timeout=12) as r: html=r.read(300000).decode("utf-8","replace")
  p=Parser();p.feed(html);image=p.meta.get("og:image") or p.meta.get("twitter:image")
  result["verification"]["source_match"]=bool(p.meta.get("og:title"))
  result["image_url"]=image
  if image and urlparse(image).scheme=="https":
   req=urllib.request.Request(image,method="HEAD",headers={"User-Agent":"Mozilla/5.0"})
   with urllib.request.urlopen(req,timeout=10) as r:
    result["verification"]["image_access"]=r.status==200 and r.headers.get("Content-Type","").startswith("image/")
 except Exception as e:result["verification_error"]=str(e)[:180]
 return result
if __name__=="__main__":
 with open(sys.argv[1],encoding="utf-8") as f:source=json.load(f)
 items=[check(x) for x in source["candidates"][:40]]
 report={"test_only":True,"published":False,"visually_reviewed":0,"source_confirmed":sum(x["verification"]["source_match"] for x in items),"image_accessible":sum(x["verification"]["image_access"] for x in items),"items":items}
 with open("free_source_verification_result.json","w",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k!="items"}))
