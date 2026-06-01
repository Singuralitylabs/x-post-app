# x-post-app

Web 技術・AI のトレンドを収集し、Google Gemini で日本語のカジュアルな X 投稿文を生成、
GitHub Issue で人間が承認してから X に自動投稿するアプリ。GitHub Actions だけで完結する。

## 仕組み

```
[generate.yml]  手動 or cron
  RSS / Hacker News / GitHub Trending を収集 → 重複除去 → Gemini で投稿文を生成(N候補)
    → 候補ごとに GitHub Issue を作成(ラベル: pending-approval)

[人間]  Issue の ```post``` ブロックを確認・編集 → `approved` ラベルを付与

[publish.yml]  on: issues(labeled: approved)
  Issue から本文を抽出 → X に投稿 → 投稿URLをコメント → Issueクローズ
    → state/seen.json に投稿済みを記録してコミット
```

状態(既読/投稿済みURL)は `state/seen.json` をリポジトリにコミットして永続化する。

## セットアップ

### 1. X API 認証情報(OAuth 1.0a)

既存の GAS 投稿アプリと同じ X Developer App を再利用できる(課金は同じ Project に集約される)。
X Developer Portal の対象 App で:

1. **User authentication settings** を開く
2. OAuth 1.0a を有効化、権限を **Read and Write** に設定
3. **Keys and tokens** から以下を発行:
   - API Key / API Key Secret(= consumer key/secret)
   - Access Token / Access Token Secret(投稿するユーザーのもの)

> 2026年2月以降、X API は従量課金。本文のみ(URL なし)なら $0.01/投稿 程度、
> URL を含む投稿は割高になり得るため、既定では URL を含めない(`INCLUDE_URL=false`)。

### 2. Gemini API キー

[Google AI Studio](https://aistudio.google.com/) で API キーを取得。

### 3. GitHub リポジトリ設定

このディレクトリを GitHub リポジトリにして push する。

**Settings → Secrets and variables → Actions** に登録:

| 種別 | 名前 |
|------|------|
| Secret | `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` |
| Secret | `GEMINI_API_KEY` |
| Variable(任意) | `GEMINI_MODEL`(既定 `gemini-2.5-flash`), `CANDIDATE_COUNT`, `INCLUDE_URL` |

`GITHUB_TOKEN` は Actions が自動提供するため登録不要。

## 使い方

### MVP(手動トリガーで検証)

1. **Actions → Generate post candidates → Run workflow** を実行
2. 作られた Issue の `post` ブロックを確認・編集
3. 問題なければ Issue に `approved` ラベルを付与 → 自動で X に投稿される

### 自動化(Phase 1)

`.github/workflows/generate.yml` の `schedule` のコメントを外すと、1日数回 cron 実行になる。

## ローカル開発

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # 値を埋める

# 収集→生成→Issue作成を dry-run(X/Issue へは書き込まない)
DRY_RUN=true python scripts/run_generate.py

# テスト(文字数カウント・URL正規化などのロジック)
pytest
```

## 収集ソースの調整

`feeds.yaml` に RSS フィードを追加・削除する。Hacker News / GitHub Trending の
取得件数は環境変数 `HN_LIMIT` / `GITHUB_TRENDING_LIMIT` で調整。

## 既存 GAS 版との違い

- 投稿元: スプレッドシートの固定リスト → ネット収集 + AI 生成
- 認証: OAuth 2.0 PKCE(GAS) → OAuth 1.0a(無期限・CI向き・将来の画像添付可)
- 承認: なし → GitHub Issue で人間承認
- 文字数カウントロジック(CJK=2)は GAS 版から移植(`src/x_post/textlen.py`)

## 構成

```
src/x_post/      … 収集・生成・投稿・Issue連携の本体
scripts/         … ワークフローのエントリポイント
.github/workflows/ … generate.yml / publish.yml
feeds.yaml       … 収集対象 RSS
state/seen.json  … 永続状態(自動コミット)
tests/           … ロジックのテスト
```
# x-post-app
