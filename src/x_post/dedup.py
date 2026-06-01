"""Filter collected articles against persistent state and topic relevance."""

from __future__ import annotations

from .models import Article

# Lightweight relevance filter for Web tech / AI focus.
KEYWORDS = (
    "ai",
    "llm",
    "gpt",
    "claude",
    "gemini",
    "machine learning",
    "ml",
    "生成ai",
    "人工知能",
    "agent",
    "rag",
    "web",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "rust",
    "python",
    "framework",
    "api",
    "開発",
    "プログラ",
    "エンジニア",
    "クラウド",
    "cloud",
    "database",
    "security",
)


def _is_relevant(article: Article) -> bool:
    # Items already tagged by a curated source/category are trusted.
    if article.category in {"ai", "web", "tech"}:
        return True
    haystack = f"{article.title} {article.summary}".lower()
    return any(k in haystack for k in KEYWORDS)


def filter_new(articles: list[Article], seen: set[str]) -> list[Article]:
    """Return relevant articles not already seen/posted."""
    result: list[Article] = []
    for a in articles:
        if a.hash in seen:
            continue
        if not _is_relevant(a):
            continue
        result.append(a)
    return result
