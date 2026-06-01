from x_post.textlen import truncate_to_limit, weighted_length, within_limit


def test_ascii_counts_one_each():
    assert weighted_length("hello") == 5


def test_japanese_counts_two_each():
    assert weighted_length("あいう") == 6


def test_mixed():
    # 3 ASCII (3) + 2 JP (4) = 7
    assert weighted_length("abcあい") == 7


def test_within_limit():
    assert within_limit("a" * 280)
    assert not within_limit("a" * 281)
    assert not within_limit("あ" * 141)  # 282 weighted


def test_truncate_keeps_within_limit():
    text = "あ" * 200  # 400 weighted
    out = truncate_to_limit(text, limit=280)
    assert weighted_length(out) <= 280
    assert out.endswith("…")
