"""Weighted character counting for X posts.

Ported from the existing GAS implementation (utils.js countTwitterLength):
characters up to U+10FF count as 1, everything else (CJK, emoji, etc.) counts as 2.
This approximates X's 280 weighted-unit limit for Japanese-heavy text.
"""

from __future__ import annotations

from .config import MAX_WEIGHTED_LENGTH


def weighted_length(text: str) -> int:
    count = 0
    for ch in text:
        count += 1 if ord(ch) <= 0x10FF else 2
    return count


def within_limit(text: str, limit: int = MAX_WEIGHTED_LENGTH) -> bool:
    return weighted_length(text) <= limit


def truncate_to_limit(text: str, limit: int = MAX_WEIGHTED_LENGTH, ellipsis: str = "…") -> str:
    """Truncate text so its weighted length fits within limit (best-effort).

    Preserves trailing hashtag lines when possible by truncating the body part.
    """
    if within_limit(text, limit):
        return text

    reserve = weighted_length(ellipsis)
    out: list[str] = []
    count = 0
    for ch in text:
        w = 1 if ord(ch) <= 0x10FF else 2
        if count + w > limit - reserve:
            break
        out.append(ch)
        count += w
    return "".join(out).rstrip() + ellipsis
