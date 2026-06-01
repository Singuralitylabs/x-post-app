#!/usr/bin/env python3
"""X API 疎通テスト。

使い方:
    python scripts/test_x_auth.py            # 認証確認のみ（投稿しない）
    python scripts/test_x_auth.py --post     # 実際に1件テスト投稿する

.env / .env.local から X_API_KEY 等4つを読み込む。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x_post.config import settings  # noqa: E402


def main() -> int:
    do_post = "--post" in sys.argv

    # 1) キーが揃っているか
    keys = {
        "X_API_KEY": settings.x_api_key,
        "X_API_SECRET": settings.x_api_secret,
        "X_ACCESS_TOKEN": settings.x_access_token,
        "X_ACCESS_TOKEN_SECRET": settings.x_access_token_secret,
    }
    print("== 認証情報の読み込み ==")
    for name, val in keys.items():
        status = f"OK (末尾 …{val[-4:]})" if val else "未設定 ✗"
        print(f"  {name}: {status}")
    missing = [n for n, v in keys.items() if not v]
    if missing:
        print(f"\n未設定のキーがあります: {', '.join(missing)}")
        print(".env または .env.local に記入してください。")
        return 1

    # 2) 認証ユーザーを取得（投稿せず権限を確認）
    import tweepy

    client = tweepy.Client(
        consumer_key=settings.x_api_key,
        consumer_secret=settings.x_api_secret,
        access_token=settings.x_access_token,
        access_token_secret=settings.x_access_token_secret,
    )
    print("\n== 認証確認（get_me）==")
    try:
        me = client.get_me(user_auth=True)
        print(f"  ログインユーザー: @{me.data.username} (id={me.data.id})")
    except Exception as exc:  # noqa: BLE001
        print(f"  失敗: {exc}")
        print("  → キーの値、または OAuth1.0a の権限設定を確認してください。")
        return 1

    # 3) 投稿テスト（--post 指定時のみ）
    if not do_post:
        print("\n投稿はスキップしました。実際に投稿するには --post を付けて再実行してください。")
        return 0

    print("\n== テスト投稿 ==")
    try:
        resp = client.create_tweet(
            text="テスト投稿: x-post-app の疎通確認 #test", user_auth=True
        )
        tweet_id = resp.data["id"]
        print(f"  成功! tweet_id={tweet_id}")
        print(f"  URL: https://x.com/i/web/status/{tweet_id}")
    except Exception as exc:  # noqa: BLE001
        print(f"  失敗: {exc}")
        print("  403 'not permitted' → 従量課金(pay-per-use)の有効化/クレジットを確認")
        print("  403 read-only 系   → 権限を Read and Write にして Access Token を再生成")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
