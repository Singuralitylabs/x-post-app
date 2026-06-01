"""Prompt templates for post generation (Japanese, casual tone)."""

from __future__ import annotations

from .models import Article

SYSTEM_INSTRUCTION = """\
あなたは Web 技術と AI のトレンドを発信する日本語の X(旧Twitter)アカウントの中の人です。
読者はエンジニアや技術に関心のある人たちです。
カジュアルで親しみやすいトーンで、でも中身は正確に。誇張・煽り・絵文字の多用は避けます。
1投稿で1つの話題を簡潔に伝えます。"""

# 出力フォーマットは既存 GAS 実装（テーマ + 本文 + ハッシュタグ）を踏襲。
POST_TEMPLATE = """\
次の記事をもとに、X に投稿する日本語のポストを1つ作ってください。

# 記事情報
タイトル: {title}
ソース: {source}
概要: {summary}
{url_line}

# 制約
- 全体で日本語120〜130文字以内（ハッシュタグ含む）。短すぎないこと。
- 出力フォーマット（プレーンテキスト、Markdown禁止）:
  1行目: 短いテーマ（10文字前後の見出し）
  空行
  本文（その話題のポイントや「なぜ面白いか」を1〜2文で）
  最後にハッシュタグを改行で2〜3個（例: #AI #Web技術）
- URLは{url_instruction}。
- 事実を捏造しない。概要から読み取れない数値や固有名詞を勝手に足さない。
- 出力はポスト本文のみ。前置きや説明は書かない。"""


def build_post_prompt(article: Article, include_url: bool) -> str:
    if include_url:
        url_line = f"URL: {article.url}"
        url_instruction = "本文の最後に1つだけ含めてよい"
    else:
        url_line = ""
        url_instruction = "含めない"
    return POST_TEMPLATE.format(
        title=article.title,
        source=article.source,
        summary=article.summary or "(概要なし。タイトルから判断)",
        url_line=url_line,
        url_instruction=url_instruction,
    )
