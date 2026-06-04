from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from collectors.market import PriceData
from collectors.web_search import search_google_news, fetch_mover_news


def make_entry(title: str, published: datetime) -> MagicMock:
    entry = MagicMock()
    entry.title = title
    entry.link = "https://news.google.com/articles/abc"
    entry.published_parsed = published.timetuple()
    return entry


@patch("collectors.web_search.feedparser.parse")
def test_search_google_news_returns_items(mock_parse):
    now = datetime.now(timezone.utc)
    mock_parse.return_value.entries = [make_entry("NVIDIA beats earnings", now - timedelta(hours=3))]
    items = search_google_news("NVDA NVIDIA stock")
    assert len(items) == 1
    assert "NVIDIA" in items[0].title


@patch("collectors.web_search.feedparser.parse")
def test_search_google_news_skips_old_items(mock_parse):
    now = datetime.now(timezone.utc)
    mock_parse.return_value.entries = [make_entry("Old article", now - timedelta(hours=72))]
    items = search_google_news("NVDA NVIDIA stock", lookback_hours=48)
    assert len(items) == 0


@patch("collectors.web_search.feedparser.parse")
def test_search_google_news_handles_error(mock_parse):
    mock_parse.side_effect = Exception("network error")
    items = search_google_news("NVDA NVIDIA stock")
    assert items == []


@patch("collectors.web_search.search_google_news")
def test_fetch_mover_news_returns_dict_by_ticker(mock_search):
    mock_search.return_value = []
    movers = [PriceData("NVDA", "NVIDIA", 900.0, 3.5)]
    result = fetch_mover_news(movers)
    assert "NVDA" in result
    mock_search.assert_called_once()


@patch("collectors.web_search.search_google_news")
def test_fetch_mover_news_tags_tickers(mock_search):
    from collectors.news import NewsItem

    now = datetime.now(timezone.utc)
    mock_search.return_value = [
        NewsItem(title="NVIDIA record earnings", url="http://x.com", source="Google News", published=now)
    ]
    movers = [PriceData("NVDA", "NVIDIA", 900.0, 3.5)]
    result = fetch_mover_news(movers)
    assert result["NVDA"][0].tickers == ["NVDA"]


@patch("collectors.web_search.search_google_news")
def test_fetch_mover_news_uses_japanese_query_for_jp_stocks(mock_search):
    mock_search.return_value = []
    movers = [PriceData("7203.T", "トヨタ自動車", 3200.0, -2.1)]
    fetch_mover_news(movers)
    call_kwargs = mock_search.call_args
    assert call_kwargs.kwargs.get("lang") == "ja" or (
        len(call_kwargs.args) > 1 and call_kwargs.args[1] == "ja"
    )
