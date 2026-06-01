from x_post.models import Article, normalize_url, url_hash


def test_normalize_strips_query_fragment_and_trailing_slash():
    a = "https://Example.com/Path/?utm=1#frag"
    b = "https://example.com/Path"
    assert normalize_url(a) == b
    assert url_hash(a) == url_hash(b)


def test_normalize_adds_default_scheme_host_lower():
    assert normalize_url("HTTPS://EXAMPLE.com/x") == "https://example.com/x"


def test_article_hash_stable():
    art = Article(title="t", url="https://example.com/a/")
    assert art.hash == url_hash("https://example.com/a")
