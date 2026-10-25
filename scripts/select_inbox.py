"""Choose the newest eligible unprocessed inbox JSON for GitHub-side publication.

This is an inbox consumer, not a bridge to ChatGPT scheduled-task output.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from normalize import normalize
from publish import validate

KST = timezone(timedelta(hours=9))

def eligible_paths(inbox, history):
    published = {item.get("day") for item in history if isinstance(item, dict)}
    result = []
    for path in sorted(Path(inbox).glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or raw.get("test_only") is True:
                continue
            entry = normalize(raw)
            day, _ = validate(entry)
            if day in published:
                continue
            result.append((day, path))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    return [p for _, p in sorted(result, key=lambda x: (x[0], x[1].name))]

def main():
    root = Path(__file__).resolve().parents[1]
    history_file = root / "data/history.json"
    history = json.loads(history_file.read_text(encoding="utf-8")) if history_file.exists() else []
    if not isinstance(history, list):
        raise SystemExit("Invalid history file")
    paths = eligible_paths(root / "inbox", history)
    if not paths:
        print("NO_ELIGIBLE_INPUT")
        return 0
    # Process one archive at a time to preserve history and prevent duplicate publication.
    print(paths[0].as_posix())
    return 0

if __name__ == "__main__":
    sys.exit(main())
