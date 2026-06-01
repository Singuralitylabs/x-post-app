#!/usr/bin/env python3
"""Entry point for the publish stage (called by publish.yml on `approved` label).

Steps: read approved Issue -> extract post text -> post to X -> comment tweet URL,
relabel & close the Issue -> record posted state.

Issue number is taken from --issue / ISSUE_NUMBER env.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x_post import issue as issue_mod  # noqa: E402
from x_post import state  # noqa: E402
from x_post.config import settings  # noqa: E402
from x_post.models import url_hash  # noqa: E402
from x_post.x_client import post_tweet  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("run_publish")

TWEET_URL = "https://x.com/i/web/status/{id}"


def _issue_number() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, default=None)
    args = parser.parse_args()
    if args.issue is not None:
        return args.issue
    env = os.environ.get("ISSUE_NUMBER")
    if env:
        return int(env)
    raise SystemExit("Issue number required (--issue or ISSUE_NUMBER)")


def main() -> int:
    number = _issue_number()
    issue = issue_mod.get_issue(number)
    log.info("publishing from issue #%d: %s", number, issue.title)

    text = issue_mod.extract_post_text(issue.body)
    source_url = issue_mod.extract_source_url(issue.body)

    tweet_id = post_tweet(text)
    tweet_url = TWEET_URL.format(id=tweet_id)

    if settings.dry_run:
        log.info("[DRY_RUN] tweet would be: %r (source %s)", text, source_url)
        return 0

    # Update the issue: comment, relabel, close.
    issue.create_comment(f"✅ 投稿しました: {tweet_url}")
    try:
        issue.remove_from_labels(settings.label_pending)
    except Exception:  # noqa: BLE001 - label may be absent
        pass
    issue.add_to_labels(settings.label_posted)
    issue.edit(state="closed")

    # Persist posted state.
    data = state.load()
    now = datetime.now(timezone.utc).isoformat()
    if source_url:
        state.mark_posted(data, url_hash(source_url), source_url, tweet_id, now)
        state.save(data)
        log.info("recorded posted state for %s", source_url)

    log.info("done: %s", tweet_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
