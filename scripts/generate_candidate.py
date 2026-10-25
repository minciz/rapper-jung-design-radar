"""Generate a review-only candidate via OpenAI API; never publish it.

Requires OPENAI_API_KEY. The model can invent sources: human/source verification
is mandatory before setting verification.source_match=true.
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))
ENDPOINT = "https://api.openai.com/v1/responses"

def extract_text(response):
    chunks = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for part in item.get("content", []):
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                chunks.append(part["text"])
    if not chunks:
        raise ValueError("API returned no output_text")
    return "\n".join(chunks)

def candidate_from_response(response, date):
    text = extract_text(response).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("Expected JSON object")
    raw["briefing_date"] = date
    raw["test_only"] = True
    refs = raw.get("references")
    if not isinstance(refs, list) or not 12 <= len(refs) <= 15:
        raise ValueError("Candidate must have 12-15 references")
    for ref in refs:
        if not isinstance(ref, dict):
            raise ValueError("Invalid reference")
        # Never treat model-provided verification as independent evidence.
        ref["verification"] = {"source_match": False, "image_access": False, "visually_reviewed": False}
        ref["image_url"] = None
    return raw

def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not configured; no paid API call made")
    date = datetime.now(KST).date().isoformat()
    model = os.environ.get("RADAR_MODEL", "gpt-5-mini")
    prompt = (
        f"Today in Korea is {date}. Research 12-15 real graphic design works around one narrow visual theme. "
        "Use web search to find original creators or studios and original work URLs. "
        "Return ONLY JSON with topic, references array (title, creator, original_page_url, recommendation, visual_features), "
        "trends array of 3 items (title, summary, checked_date, source_urls). "
        "Do not invent URLs or claim verification; missing evidence should be explicit. "
        "This is an unverified editorial draft, NOT a publication-ready archive."
    )
    payload = {"model": model, "tools": [{"type": "web_search"}], "input": prompt,
               "text": {"format": {"type": "json_object"}}}
    req = Request(ENDPOINT, data=json.dumps(payload).encode(), method="POST",
                  headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                           "Content-Type": "application/json"})
    with urlopen(req, timeout=180) as resp:
        result = json.load(resp)
    candidate = candidate_from_response(result, date)
    path = Path("inbox") / f"candidate_{date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created review-only candidate: {path}")

if __name__ == "__main__":
    main()
