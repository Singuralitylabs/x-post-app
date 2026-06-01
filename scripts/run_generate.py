#!/usr/bin/env python3
"""Entry point for the generate stage (called by generate.yml or locally).

Steps: collect -> dedup against state -> generate candidates with Gemini
-> create one approval Issue per candidate -> mark seen and persist state.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running without `pip install -e .`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x_post import dedup, state  # noqa: E402
from x_post.collect import collect_all  # noqa: E402
from x_post.config import settings  # noqa: E402
from x_post.generate import generate_candidates  # noqa: E402
from x_post.issue import create_candidate_issues  # noqa: E402
from x_post.models import url_hash  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("run_generate")


def main() -> int:
    log.info(
        "config: candidates=%d include_url=%s dry_run=%s model=%s",
        settings.candidate_count,
        settings.include_url,
        settings.dry_run,
        settings.gemini_model,
    )

    articles = collect_all()
    log.info("collected %d unique articles", len(articles))

    data = state.load()
    seen = state.seen_hashes(data)
    fresh = dedup.filter_new(articles, seen)
    log.info("%d fresh & relevant articles after dedup", len(fresh))

    if not fresh:
        log.info("nothing new to post; exiting")
        return 0

    candidates = generate_candidates(fresh)
    log.info("generated %d candidates", len(candidates))
    if not candidates:
        return 0

    numbers = create_candidate_issues(candidates)
    log.info("created issues: %s", numbers)

    # Mark the source articles as seen so they don't resurface next run.
    now = datetime.now(timezone.utc).isoformat()
    for c in candidates:
        state.mark_seen(data, url_hash(c.article_url), c.article_url, now)
    if not settings.dry_run:
        state.save(data)
        log.info("state saved")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
