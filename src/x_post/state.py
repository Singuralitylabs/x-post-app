"""Persistent state stored in state/seen.json (committed back by the workflow).

Schema:
    {
      "seen":   [ {"hash": ..., "url": ..., "ts": ...}, ... ],  # surfaced as candidates
      "posted": [ {"hash": ..., "url": ..., "tweet_id": ..., "ts": ...}, ... ]
    }
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import STATE_PATH

# Cap history so the file does not grow unbounded.
MAX_HISTORY = 1000


def load(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {"seen": [], "posted": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"seen": [], "posted": []}
    data.setdefault("seen", [])
    data.setdefault("posted", [])
    return data


def save(data: dict, path: Path = STATE_PATH) -> None:
    data["seen"] = data.get("seen", [])[-MAX_HISTORY:]
    data["posted"] = data.get("posted", [])[-MAX_HISTORY:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def seen_hashes(data: dict) -> set[str]:
    hashes = {e.get("hash") for e in data.get("seen", [])}
    hashes |= {e.get("hash") for e in data.get("posted", [])}
    hashes.discard(None)
    return hashes  # type: ignore[return-value]


def mark_seen(data: dict, hash_: str, url: str, ts: str = "") -> None:
    data.setdefault("seen", []).append({"hash": hash_, "url": url, "ts": ts})


def mark_posted(data: dict, hash_: str, url: str, tweet_id: str, ts: str = "") -> None:
    data.setdefault("posted", []).append(
        {"hash": hash_, "url": url, "tweet_id": tweet_id, "ts": ts}
    )
