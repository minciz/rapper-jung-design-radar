"""Free-source discovery probe. No paid API, no publication, no image copying."""
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlparse

FEEDS = {
    "Creative Boom": "https://www.creativeboom.com/feed/",
    "Creative Bloq": "https://www.creativebloq.com/feeds/all",
    "Designboom": "https://www.designboom.com/feed/",
    "The Brand Identity": "https://the-brandidentity.com/feed",
    "Design Milk": "https://design-milk.com/feed/",
    "Creative Review": "https://www.creativereview.co.uk/feed/",
}
UA = {"User-Agent": "DesignRadarResearchProbe/0.1 (+source-link-only)"}

def probe():
    report = {"tested_at_utc": datetime.now(timezone.utc).isoformat(),
              "test_only": True, "published": False, "sources": [], "candidates": []}
    seen = set()
    for name, address in FEEDS.items():
        item = {"name": name, "feed": address, "status": "failed", "entries": 0}
        try:
            request = urllib.request.Request(address, headers=UA)
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = response.read(2_000_000)
            root = ET.fromstring(payload)
            entries = root.findall(".//item")
            if not entries:
                atom = "{http://www.w3.org/2005/Atom}"
                entries = root.findall(".//" + atom + "entry")
            item["entries"] = len(entries)
            item["status"] = "ok"
            for entry in entries:
                title = (entry.findtext("title") or entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                link = (entry.findtext("link") or "").strip()
                if not link:
                    node = entry.find("{http://www.w3.org/2005/Atom}link")
                    link = node.get("href", "") if node is not None else ""
                parsed = urlparse(link)
                if not title or parsed.scheme not in ("https", "http") or not parsed.netloc:
                    continue
                key = link.rstrip("/").lower()
                if key in seen:
                    continue
                seen.add(key)
                report["candidates"].append({"title": title, "source_url": link,
                  "source_feed": name, "verification": {"source_match": False,
                  "image_access": False, "visually_reviewed": False}})
        except Exception as exc:
            item["error"] = str(exc)[:300]
        report["sources"].append(item)
    return report

if __name__ == "__main__":
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
