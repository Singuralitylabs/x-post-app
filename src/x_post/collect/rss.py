"""RSS/Atom collector using feedparser."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser

from ..config import load_feeds
from ..models import Article

log = logging.getLogger(__name__)

# Only keep entries newer than this many days (0 = no filter).
MAX_AGE_DAYS = 7
# Entries to take per feed.
PER_FEED = 5


def _published_iso(entry) -> str:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return ""
    try:
        return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return ""


def _is_recent(iso: str) -> bool:
    if MAX_AGE_DAYS <= 0 or not iso:
        return True
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return True
    age = datetime.now(timezone.utc) - dt
    return age.days <= MAX_AGE_DAYS


def _clean_summary(raw: str, limit: int = 500) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def collect() -> list[Article]:
    articles: list[Article] = []
    for feed in load_feeds():
        url = feed.get("url")
        if not url:
            continue
        name = feed.get("name", url)
        category = feed.get("category", "")
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:  # noqa: BLE001
            log.warning("feed parse failed %s: %s", name, exc)
            continue

        count = 0
        for entry in parsed.entries:
            link = entry.get("link", "")
            title = entry.get("title", "").strip()
            if not link or not title:
                continue
            iso = _published_iso(entry)
            if not _is_recent(iso):
                continue
            articles.append(
                Article(
                    title=title,
                    url=link,
                    summary=_clean_summary(entry.get("summary", "")),
                    source=name,
                    category=category,
                    published_at=iso,
                )
            )
            count += 1
            if count >= PER_FEED:
                break
    return articles
