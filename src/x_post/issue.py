"""GitHub Issue creation/parsing for the approval workflow (PyGithub).

A generate run creates one Issue per candidate so each can be approved
independently by adding the `approved` label. The final post text lives in a
fenced ```post block``` so a reviewer can edit it before approving, and
publish can extract it deterministically.
"""

from __future__ import annotations

import logging
import re

from github import Github

from .config import settings
from .models import Candidate

log = logging.getLogger(__name__)

POST_BLOCK_RE = re.compile(r"```post\s*\n(.*?)```", re.DOTALL)
SOURCE_LINE_RE = re.compile(r"^<!--\s*source:\s*(\S+)\s*-->", re.MULTILINE)

ISSUE_BODY_TEMPLATE = """\
<!-- source: {url} -->
AI が生成した X 投稿の下書きです。下の `post` ブロックを必要に応じて編集し、\
問題なければ `{label_approved}` ラベルを付けると自動投稿されます。

**投稿本文（このブロックの中身がそのまま投稿されます）:**

```post
{text}
```

---
- 出典: [{title}]({url})
- ソース: {source}
- 加重文字数: {length} / 280
- メモ: {notes}
"""


def _repo():
    settings.require_github()
    gh = Github(settings.github_token)
    return gh.get_repo(settings.github_repository)


def _ensure_label(repo, name: str, color: str) -> None:
    try:
        repo.get_label(name)
    except Exception:  # noqa: BLE001 - label missing
        try:
            repo.create_label(name=name, color=color)
        except Exception as exc:  # noqa: BLE001 - race or perms; non-fatal
            log.debug("could not create label %s: %s", name, exc)


def create_candidate_issues(candidates: list[Candidate]) -> list[int]:
    """Create one pending-approval Issue per candidate. Returns issue numbers.

    In dry-run mode, GitHub is never contacted; bodies are logged instead.
    """
    # Connect to GitHub only when actually creating issues.
    repo = None
    if not settings.dry_run:
        repo = _repo()
        _ensure_label(repo, settings.label_pending, "fbca04")
        _ensure_label(repo, settings.label_approved, "0e8a16")
        _ensure_label(repo, settings.label_posted, "5319e7")

    numbers: list[int] = []
    for c in candidates:
        title = f"[投稿候補] {c.article_title[:60]}"
        body = ISSUE_BODY_TEMPLATE.format(
            url=c.article_url,
            text=c.text,
            title=c.article_title or c.article_url,
            source=c.source,
            length=c.weighted_length,
            notes=c.notes or "なし",
            label_approved=settings.label_approved,
        )
        if settings.dry_run:
            log.info("[DRY_RUN] would create issue: %s\n%s", title, body)
            continue
        issue = repo.create_issue(
            title=title, body=body, labels=[settings.label_pending]
        )
        numbers.append(issue.number)
        log.info("created issue #%d", issue.number)
    return numbers


def extract_post_text(body: str) -> str:
    """Pull the final post text from an issue body's ```post``` block."""
    m = POST_BLOCK_RE.search(body or "")
    if not m:
        raise ValueError("No ```post``` block found in issue body")
    return m.group(1).strip()


def extract_source_url(body: str) -> str:
    m = SOURCE_LINE_RE.search(body or "")
    return m.group(1) if m else ""


def get_issue(number: int):
    return _repo().get_issue(number)
