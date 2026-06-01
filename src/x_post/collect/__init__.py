"""Source collectors. Each returns a list of normalized Article objects."""

from __future__ import annotations

import logging

from ..config import settings
from ..models import Article
from . import github_trending, hackernews, rss

log = logging.getLogger(__name__)


def collect_all() -> list[Article]:
    """Run every collector, tolerating individual source failures."""
    articles: list[Article] = []
    for name, fn in (
        ("rss", rss.collect),
        ("hackernews", hackernews.collect),
        ("github_trending", github_trending.collect),
    ):
        try:
            items = fn()
            log.info("collector %s returned %d items", name, len(items))
            articles.extend(items)
        except Exception as exc:  # noqa: BLE001 - one bad source must not abort the run
            log.warning("collector %s failed: %s", name, exc)

    # De-duplicate within this run by URL hash, keep first occurrence.
    seen: set[str] = set()
    unique: list[Article] = []
    for a in articles:
        if not a.url or a.hash in seen:
            continue
        seen.add(a.hash)
        unique.append(a)

    return unique[: settings.max_articles]
