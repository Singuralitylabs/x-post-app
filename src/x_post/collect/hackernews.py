"""Hacker News collector using the public Firebase API."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from ..config import settings
from ..models import Article

log = logging.getLogger(__name__)

TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
HN_ITEM_URL = "https://news.ycombinator.com/item?id={id}"

# Skip low-signal posts.
MIN_SCORE = 50
TIMEOUT = 15


def collect() -> list[Article]:
    limit = settings.hn_limit
    try:
        ids = requests.get(TOP_STORIES, timeout=TIMEOUT).json() or []
    except Exception as exc:  # noqa: BLE001
        log.warning("HN topstories fetch failed: %s", exc)
        return []

    articles: list[Article] = []
    for story_id in ids[: limit * 3]:  # over-fetch, then filter by score
        if len(articles) >= limit:
            break
        try:
            item = requests.get(ITEM.format(id=story_id), timeout=TIMEOUT).json()
        except Exception as exc:  # noqa: BLE001
            log.debug("HN item %s failed: %s", story_id, exc)
            continue
        if not item or item.get("type") != "story":
            continue
        if item.get("score", 0) < MIN_SCORE:
            continue
        title = item.get("title", "").strip()
        if not title:
            continue
        # Prefer the external article URL; fall back to the HN discussion.
        url = item.get("url") or HN_ITEM_URL.format(id=story_id)
        ts = item.get("time")
        iso = (
            datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ""
        )
        articles.append(
            Article(
                title=title,
                url=url,
                summary=f"Hacker News score {item.get('score', 0)}, "
                f"{item.get('descendants', 0)} comments.",
                source="Hacker News",
                category="tech",
                published_at=iso,
            )
        )
    return articles
