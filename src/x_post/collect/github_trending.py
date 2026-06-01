"""GitHub Trending collector.

GitHub has no official Trending API, so we scrape the public trending page.
This is best-effort: any failure returns [] and the pipeline continues.
"""

from __future__ import annotations

import logging
import re

import requests

from ..config import settings
from ..models import Article

log = logging.getLogger(__name__)

TRENDING_URL = "https://github.com/trending?since=daily"
TIMEOUT = 15
HEADERS = {"User-Agent": "x-post-app/0.1 (+https://github.com)"}

# Matches the repo anchor like <a href="/owner/repo" ...> on the trending page.
_REPO_RE = re.compile(r'<h2[^>]*>\s*<a href="/([^/"]+/[^/"]+)"', re.IGNORECASE)


def collect() -> list[Article]:
    limit = settings.github_trending_limit
    try:
        resp = requests.get(TRENDING_URL, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        log.warning("GitHub trending fetch failed: %s", exc)
        return []

    html = resp.text
    repos: list[str] = []
    for match in _REPO_RE.finditer(html):
        slug = match.group(1).strip()
        if slug and slug not in repos:
            repos.append(slug)
        if len(repos) >= limit:
            break

    articles: list[Article] = []
    for slug in repos:
        owner, _, repo = slug.partition("/")
        articles.append(
            Article(
                title=f"{repo} ({owner})",
                url=f"https://github.com/{slug}",
                summary=f"GitHub Trending (daily): {slug}",
                source="GitHub Trending",
                category="web",
                published_at="",
            )
        )
    return articles
