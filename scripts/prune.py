"""Remove records older than 30 days (Korean local time is supported via ISO offsets)."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'data' / 'entries.json'
records = json.loads(path.read_text(encoding='utf-8'))
if not isinstance(records, list):
    raise ValueError('entries.json must contain an array')
now = datetime.now(timezone.utc)
kept = []
for item in records:
    try:
        stamp = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            continue
        age = now - stamp.astimezone(timezone.utc)
        if timedelta(0) <= age < timedelta(days=30):
            kept.append(item)
    except (KeyError, TypeError, ValueError, AttributeError):
        continue
if kept != records:
    path.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Retained {len(kept)} of {len(records)} entries')
