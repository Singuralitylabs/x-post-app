"""Configuration loaded from environment variables and feeds.yaml.

Loads a local .env if python-dotenv is available, but does not require it
(GitHub Actions provides env vars directly).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

# Project root = two levels up from this file (src/x_post/config.py -> repo root)
ROOT = Path(__file__).resolve().parents[2]
FEEDS_PATH = ROOT / "feeds.yaml"
STATE_PATH = ROOT / "state" / "seen.json"

# X post weighted-length limit (matches X 280 weighted units).
MAX_WEIGHTED_LENGTH = 280


def _load_dotenv() -> None:
    """Best-effort load of a local env file without a hard dependency.

    Reads .env and .env.local if present (.env.local wins on duplicates only
    over .env, never over real environment variables).
    """
    for name in (".env", ".env.local"):
        env_file = ROOT / name
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Do not override values already present in the real environment.
            os.environ.setdefault(key, value)


_load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip())
    except (TypeError, ValueError):
        return default


def _str(name: str, default: str = "") -> str:
    """Return env var, treating empty/whitespace as unset.

    GitHub Actions passes unset `${{ vars.X }}` as an empty string, which would
    otherwise override a sensible default. Falling back on blank avoids that.
    """
    val = os.environ.get(name)
    if val is None or not val.strip():
        return default
    return val.strip()


@dataclass(frozen=True)
class Settings:
    # X API (OAuth 1.0a)
    x_api_key: str = os.environ.get("X_API_KEY", "")
    x_api_secret: str = os.environ.get("X_API_SECRET", "")
    x_access_token: str = os.environ.get("X_ACCESS_TOKEN", "")
    x_access_token_secret: str = os.environ.get("X_ACCESS_TOKEN_SECRET", "")

    # Gemini
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    gemini_model: str = _str("GEMINI_MODEL", "gemini-2.5-flash")

    # GitHub
    github_token: str = os.environ.get("GITHUB_TOKEN", "")
    github_repository: str = os.environ.get("GITHUB_REPOSITORY", "")

    # Behavior
    candidate_count: int = _int("CANDIDATE_COUNT", 3)
    include_url: bool = _bool("INCLUDE_URL", False)
    dry_run: bool = _bool("DRY_RUN", False)

    # Collection tuning
    hn_limit: int = _int("HN_LIMIT", 15)
    github_trending_limit: int = _int("GITHUB_TRENDING_LIMIT", 10)
    max_articles: int = _int("MAX_ARTICLES", 40)

    # Issue labels
    label_pending: str = _str("LABEL_PENDING", "pending-approval")
    label_approved: str = _str("LABEL_APPROVED", "approved")
    label_posted: str = _str("LABEL_POSTED", "posted")

    def require_x(self) -> None:
        missing = [
            n
            for n, v in {
                "X_API_KEY": self.x_api_key,
                "X_API_SECRET": self.x_api_secret,
                "X_ACCESS_TOKEN": self.x_access_token,
                "X_ACCESS_TOKEN_SECRET": self.x_access_token_secret,
            }.items()
            if not v
        ]
        if missing:
            raise RuntimeError(f"Missing X API credentials: {', '.join(missing)}")

    def require_gemini(self) -> None:
        if not self.gemini_api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")

    def require_github(self) -> None:
        if not self.github_token:
            raise RuntimeError("Missing GITHUB_TOKEN")
        if not self.github_repository:
            raise RuntimeError("Missing GITHUB_REPOSITORY (owner/repo)")


def load_feeds() -> list[dict]:
    """Load feed definitions from feeds.yaml. Returns [] if absent."""
    if not FEEDS_PATH.exists():
        return []
    data = yaml.safe_load(FEEDS_PATH.read_text(encoding="utf-8")) or {}
    return data.get("feeds", [])


settings = Settings()
