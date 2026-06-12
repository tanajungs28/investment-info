from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from collectors.news import fetch_rss_news, fetch_yfinance_news, match_tickers, collect_news, NewsItem


def make_entry(title: str, published: datetime) -> MagicMock:
    entry = MagicMock()
    entry.title = title
    entry.link = "https://example.com/news"
    entry.published_parsed = published.timetuple()
    return entry


@patch("collectors.news.feedparser.parse")
def test_fetch_rss_keeps_only_last_24h(mock_parse):
    now = datetime.now(timezone.utc)
    recent = make_entry("Recent news", now - timedelta(hours=12))
    old = make_entry("Old news", now - timedelta(hours=36))
    mock_parse.return_value.entries = [recent, old]
    items = fetch_rss_news("http://example.com/rss", "Test Source", lookback_hours=24)
    assert len(items) == 1
    assert items[0].title == "Recent news"


@patch("collectors.news.feedparser.parse")
def test_fetch_rss_falls_back_to_updated_date_for_rdf_feeds(mock_parse):
    now = datetime.now(timezone.utc)
    entry = MagicMock()
    entry.title = "RDF形式のニュース"
    entry.link = "https://example.com/rdf-news"
    entry.published_parsed = None
    entry.updated_parsed = (now - timedelta(hours=1)).timetuple()
    mock_parse.return_value.entries = [entry]
    items = fetch_rss_news("http://example.com/rdf", "Test Source", lookback_hours=24)
    assert len(items) == 1
    assert items[0].title == "RDF形式のニュース"


def test_match_tickers_finds_company_name():
    watchlist = [{"ticker": "NVDA", "name": "NVIDIA"}]
    item = NewsItem(
        title="NVIDIAが新型GPUを発表",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert "NVDA" in result[0].tickers


def test_match_tickers_finds_ticker_symbol():
    watchlist = [{"ticker": "AAPL", "name": "Apple"}]
    item = NewsItem(
        title="AAPL hits record high",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert "AAPL" in result[0].tickers


def test_fetch_yfinance_news_returns_items():
    stocks = [{"ticker": "NVDA", "name": "NVIDIA"}]
    mock_article = {
        "title": "NVIDIA posts record earnings",
        "link": "https://example.com/nvda-earnings",
        "publisher": "Reuters",
        "providerPublishTime": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
    }
    with patch("collectors.news.yf.Ticker") as mock_ticker_cls:
        mock_ticker = MagicMock()
        mock_ticker.news = [mock_article]
        mock_ticker_cls.return_value = mock_ticker
        items = fetch_yfinance_news(stocks)
    assert len(items) == 1
    assert items[0].title == "NVIDIA posts record earnings"
    assert "NVDA" in items[0].tickers


def test_fetch_yfinance_news_skips_old_articles():
    stocks = [{"ticker": "AAPL", "name": "Apple"}]
    old_article = {
        "title": "Old news",
        "link": "https://example.com/old",
        "publisher": "Reuters",
        "providerPublishTime": int((datetime.now(timezone.utc) - timedelta(hours=72)).timestamp()),
    }
    with patch("collectors.news.yf.Ticker") as mock_ticker_cls:
        mock_ticker = MagicMock()
        mock_ticker.news = [old_article]
        mock_ticker_cls.return_value = mock_ticker
        items = fetch_yfinance_news(stocks, lookback_hours=48)
    assert len(items) == 0


def test_match_tickers_finds_japanese_alias():
    watchlist = [{"ticker": "NVDA", "name": "NVIDIA", "aliases": ["エヌビディア"]}]
    item = NewsItem(
        title="エヌビディア、新型GPUを発表",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert "NVDA" in result[0].tickers


def test_match_tickers_short_ticker_does_not_match_inside_word():
    watchlist = [{"ticker": "MO", "name": "Altria Group"}]
    item = NewsItem(
        title="MORNING market update for investors",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert result[0].tickers == []


def test_match_tickers_short_ticker_matches_as_standalone_word():
    watchlist = [{"ticker": "MO", "name": "Altria Group"}]
    item = NewsItem(
        title="MO shares rise after dividend hike",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert "MO" in result[0].tickers


def test_match_tickers_strips_dot_t_for_jp_stocks():
    watchlist = [{"ticker": "7203.T", "name": "トヨタ自動車"}]
    item = NewsItem(
        title="トヨタ自動車が増産を発表",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert "7203.T" in result[0].tickers
