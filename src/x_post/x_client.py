"""Thin wrapper around tweepy for posting to X (OAuth 1.0a user context).

OAuth 1.0a access tokens do not expire, which suits stateless GitHub Actions
runs and also enables future media uploads (v1.1 endpoint requires OAuth 1.0a).
"""

from __future__ import annotations

import logging

import tweepy

from .config import settings
from .textlen import weighted_length, within_limit

log = logging.getLogger(__name__)


def _client() -> tweepy.Client:
    settings.require_x()
    return tweepy.Client(
        consumer_key=settings.x_api_key,
        consumer_secret=settings.x_api_secret,
        access_token=settings.x_access_token,
        access_token_secret=settings.x_access_token_secret,
    )


def post_tweet(text: str) -> str:
    """Post a tweet and return its tweet id. Raises on failure."""
    if not text.strip():
        raise ValueError("Empty tweet text")
    if not within_limit(text):
        raise ValueError(
            f"Tweet exceeds weighted limit: {weighted_length(text)} units"
        )

    if settings.dry_run:
        log.info("[DRY_RUN] would post: %r", text)
        return "DRY_RUN"

    client = _client()
    # OAuth 1.0a user context（consumer + access token）で投稿。
    resp = client.create_tweet(text=text, user_auth=True)
    tweet_id = str(resp.data["id"])
    log.info("posted tweet %s", tweet_id)
    return tweet_id
