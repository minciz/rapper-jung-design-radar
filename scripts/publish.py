"""Validate and publish a 15-reference daily archive from an incoming JSON file.
Usage: python scripts/publish.py path/to/day.json
This command does not connect to a ChatGPT scheduled task.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
from normalize import normalize

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "entries.json"
HISTORY = ROOT / "data" / "history.json"
KST = timezone(timedelta(hours=9))

def url(value):
    return isinstance(value, str) and urlparse(value).scheme in ("http", "https") and bool(urlparse(value).netloc)

def required(record, name):
    if not isinstance(record.get(name), str) or not record[name].strip():
        raise ValueError(f"Missing {name}")

def validate(entry):
    if not isinstance(entry, dict):
        raise ValueError("Archive must be a JSON object")
    required(entry, "date")
    try:
        dt = datetime.fromisoformat(entry["date"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid ISO date") from exc
    if dt.tzinfo is None:
        raise ValueError("Date must include timezone")
    if dt.astimezone(timezone.utc) > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise ValueError("Future date")
    required(entry, "theme")
    refs = entry.get("references")
    if not isinstance(refs, list) or not 1 <= len(refs) <= 15:
        raise ValueError("1–15 references required")
    seen = set()
    for index, ref in enumerate(refs, 1):
        if not isinstance(ref, dict):
            raise ValueError(f"Reference {index} is not an object")
        required(ref, "title")
        for key in ("image_url", "source_url"):
            value = ref.get(key)
            if value is not None and not url(value):
                raise ValueError(f"Reference {index}: invalid {key}")
        if not ref.get("source_url") and not ref.get("verification_reason"):
            raise ValueError(f"Reference {index}: missing source URL requires verification_reason")
        if not ref.get("image_url") and not ref.get("verification_reason"):
            raise ValueError(f"Reference {index}: missing image URL requires verification_reason")
        # A single exhibition page can legitimately describe multiple works.
        # Prefer distinct image URLs; fall back to work identity for missing images.
        canonical = (ref.get("image_url") or (ref["title"].strip().casefold() + "|" + str(ref.get("creator", "")).strip().casefold())).rstrip("/").casefold()
        if canonical in seen:
            raise ValueError("Duplicate work within archive")
        seen.add(canonical)
    signals = entry.get("signals")
    if not isinstance(signals, list) or not 3 <= len(signals) <= 5:
        raise ValueError("3–5 signals required")
    for s in signals:
        if not isinstance(s, dict):
            raise ValueError("Signal must be an object")
        required(s, "title")
        required(s, "summary")
        required(s, "checked_at")
        if s.get("source_url") is not None and not url(s["source_url"]):
            raise ValueError("Invalid signal URL")
    return dt.astimezone(KST).date().isoformat(), seen

def load(path, fallback):
    if not path.exists():
        return fallback
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"{path.name} must be an array")
    return value

def publish(entry, data_path=DATA, history_path=HISTORY):
    day, urls = validate(entry)
    current = load(data_path, [])
    history = load(history_path, [])
    if any(isinstance(x, dict) and x.get("day") == day for x in history):
        raise ValueError(f"Already published: {day}")
    known = {u for item in history if isinstance(item, dict) for u in item.get("urls", [])}
    repeated = urls & known
    if repeated:
        raise ValueError(f"Previously published work: {sorted(repeated)[0]}")
    # Validate all before writing either file. Atomic replacement per file.
    updated = [x for x in current if isinstance(x, dict) and x.get("date") != entry["date"]] + [entry]
    record = {"day": day, "urls": sorted(urls)}
    new_history = history + [record]
    for path, value in ((data_path, updated), (history_path, new_history)):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
    return day

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/publish.py daily.json")
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    daily = normalize(raw)
    print("Published", publish(daily))
