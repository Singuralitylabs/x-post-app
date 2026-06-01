"""Post generation via Google Gemini (google-genai SDK).

Generates one post per selected article. Google Search grounding is enabled
for freshness when available, with a graceful fallback when the tool is not
supported by the chosen model.
"""

from __future__ import annotations

import logging

from google import genai
from google.genai import types

from .config import settings
from .models import Article, Candidate
from .prompts import SYSTEM_INSTRUCTION, build_post_prompt
from .textlen import truncate_to_limit, weighted_length

log = logging.getLogger(__name__)


def _extract_grounding(response) -> str:
    """Best-effort extraction of grounding source titles for the Issue notes."""
    try:
        meta = response.candidates[0].grounding_metadata
        chunks = getattr(meta, "grounding_chunks", None) or []
        titles = []
        for c in chunks:
            web = getattr(c, "web", None)
            if web and getattr(web, "title", None):
                titles.append(web.title)
        if titles:
            return "grounding: " + ", ".join(titles[:3])
    except (AttributeError, IndexError, TypeError):
        pass
    return ""


def _generate_text(client: genai.Client, prompt: str) -> tuple[str, str]:
    """Return (text, notes). Tries grounding first, falls back to plain."""
    base_config = dict(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.85,
    )
    # Attempt with Google Search grounding.
    try:
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            **base_config,
        )
        resp = client.models.generate_content(
            model=settings.gemini_model, contents=prompt, config=config
        )
        return (resp.text or "").strip(), _extract_grounding(resp)
    except Exception as exc:  # noqa: BLE001
        log.warning("grounded generation failed, retrying plain: %s", exc)

    config = types.GenerateContentConfig(**base_config)
    resp = client.models.generate_content(
        model=settings.gemini_model, contents=prompt, config=config
    )
    return (resp.text or "").strip(), ""


def generate_candidates(articles: list[Article]) -> list[Candidate]:
    """Generate up to settings.candidate_count post candidates."""
    settings.require_gemini()
    client = genai.Client(api_key=settings.gemini_api_key)

    candidates: list[Candidate] = []
    for article in articles:
        if len(candidates) >= settings.candidate_count:
            break
        prompt = build_post_prompt(article, settings.include_url)
        try:
            text, notes = _generate_text(client, prompt)
        except Exception as exc:  # noqa: BLE001 - skip this article, keep going
            log.warning("generation failed for %s: %s", article.url, exc)
            continue
        if not text:
            continue

        text = truncate_to_limit(text)
        candidates.append(
            Candidate(
                text=text,
                article_url=article.url,
                article_title=article.title,
                source=article.source,
                weighted_length=weighted_length(text),
                notes=notes,
            )
        )
        log.info("generated candidate (%d units) from %s", weighted_length(text), article.source)

    return candidates
