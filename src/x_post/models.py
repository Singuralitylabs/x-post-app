"""Shared data structures used across the pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from urllib.parse import urlsplit, urlunsplit


def normalize_url(url: str) -> str:
    """Normalize a URL for stable dedup hashing.

    Drops query/fragment and trailing slash, lowercases scheme/host.
    """
    if not url:
        return ""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    return urlunsplit((scheme, netloc, path, "", ""))


def url_hash(url: str) -> str:
    """Stable short hash of a normalized URL."""
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()[:16]


@dataclass
class Article:
    """A normalized item collected from any source."""

    title: str
    url: str
    summary: str = ""
    source: str = ""
    category: str = ""
    published_at: str = ""  # ISO 8601 string when available

    @property
    def hash(self) -> str:
        return url_hash(self.url)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Candidate:
    """A generated post candidate awaiting approval."""

    text: str  # final post body (theme + body + hashtags), no URL by default
    article_url: str  # source url for reference / dedup
    article_title: str = ""
    source: str = ""
    weighted_length: int = 0
    notes: str = ""  # e.g. grounding sources, warnings

    def to_dict(self) -> dict:
        return asdict(self)
