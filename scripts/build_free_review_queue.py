"""Create a transparent review queue, NOT a visually curated or publishable list."""
import json, re, sys
from collections import Counter

TERMS = {
    "graphic": 6, "typograph": 7, "poster": 7, "illustrat": 5,
    "identity": 6, "branding": 6, "brand": 4, "logo": 5,
    "packaging": 6, "editorial": 6, "print": 4, "design": 3,
    "visual": 4, "collage": 6, "artwork": 4, "typeface": 7,
    "photograph": 2, "campaign": 4, "creative": 2
}
EXCLUDE = ("shopping guide", "gift guide", "sale", "discount", "buy now")

def rank(item):
    title = item.get("title", "").lower()
    score = sum(weight for word, weight in TERMS.items() if word in title)
    if any(term in title for term in EXCLUDE):
        score -= 15
    verified = item.get("verification", {})
    if not (verified.get("source_match") and verified.get("image_access")):
        score -= 100
    return score

def shortlist(items, limit=15):
    candidates = [x for x in items if rank(x) >= 0]
    candidates.sort(key=lambda x: (-rank(x), x.get("source_feed", ""), x.get("source_url", "")))
    sources = list(dict.fromkeys(x.get("source_feed", "") for x in candidates))
    selected, counts, seen = [], Counter(), set()
    while len(selected) < limit:
        available = [x for x in candidates if x["source_url"] not in seen]
        if not available:
            break
        available.sort(key=lambda x: (counts[x.get("source_feed", "")], -rank(x), x["source_url"]))
        chosen = available[0]
        seen.add(chosen["source_url"])
        counts[chosen.get("source_feed", "")] += 1
        selected.append({
            "title": chosen["title"], "source_url": chosen["source_url"],
            "image_url": chosen.get("image_url"), "source_feed": chosen.get("source_feed"),
            "automated_relevance_score": rank(chosen),
            "review_status": "pending_human_visual_and_editorial_review",
            "eligible_for_publish": False
        })
    return selected

if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    picks = shortlist(data["items"])
    result = {
        "test_only": True, "published": False,
        "selection_type": "automated_preliminary_review_queue_not_curated",
        "visual_reviews_completed": 0, "target_count": 15,
        "candidate_count": len(data["items"]), "queued_count": len(picks),
        "items": picks
    }
    with open("free_source_review_queue.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({k:v for k,v in result.items() if k != "items"}, ensure_ascii=False))
