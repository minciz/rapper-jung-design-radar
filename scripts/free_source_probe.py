"""Free-source discovery probe. No paid API, no publication, no image copying."""
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlparse

FEEDS = {
    "Creative Boom": "https://www.creativeboom.com/feed/",
    "It's Nice That": "https://www.itsnicethat.com/rss",
    "Design Milk": "https://design-milk.com/feed/",
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
            item["entries"] = len(entries)
            item["status"] = "ok"
            for entry in entries:
                title = (entry.findtext("title") or "").strip()
                link = (entry.findtext("link") or "").strip()
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
