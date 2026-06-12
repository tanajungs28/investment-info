from unittest.mock import patch
from datetime import datetime, timezone
from main import load_config, run


def test_load_config_has_required_keys():
    config = load_config()
    assert "indices" in config["watchlist"]
    assert "stocks" in config["watchlist"]
    assert "sectors" in config["watchlist"]
    assert "slack" in config["settings"]
    assert "news" in config["settings"]


@patch("main.post_report", return_value=True)
@patch("main.generate_summary", return_value=None)
@patch("main.parse_forex_factory_events", return_value=[])
@patch("main.collect_news", return_value=[])
@patch("main.get_market_data")
def test_run_calls_all_collectors_and_returns_true(
    mock_market, mock_news, mock_calendar, mock_summary, mock_post
):
    mock_market.return_value = {
        "indices": [], "forex": [], "us_stocks": [],
        "jp_stocks": [], "us_sectors": [], "jp_sectors": [],
        "timestamp": datetime.now(timezone.utc),
    }
    result = run(
        webhook_url="https://hooks.slack.com/test",
        anthropic_api_key="test-key",
    )
    assert result is True
    assert mock_market.called
    assert mock_news.called
    assert mock_calendar.called
    assert mock_post.called


@patch("main.post_report", return_value=True)
@patch("main.generate_summary", return_value=None)
@patch("main.parse_forex_factory_events", return_value=[])
@patch("main.collect_news", return_value=[])
@patch("main.get_market_data")
def test_run_passes_volume_anomalies_to_report(
    mock_market, mock_news, mock_calendar, mock_summary, mock_post
):
    from collectors.market import PriceData

    spiking = PriceData("WDC", "Western Digital", 55.0, 0.4,
                        volume=40_000_000, avg_volume=10_000_000)
    mock_market.return_value = {
        "indices": [], "forex": [], "us_stocks": [spiking],
        "jp_stocks": [], "us_sectors": [], "jp_sectors": [],
        "timestamp": datetime.now(timezone.utc),
    }
    run(webhook_url="https://hooks.slack.com/test", anthropic_api_key="test-key")
    posted = mock_post.call_args.kwargs["data"]
    assert "volume_anomalies" in posted
    assert [s.ticker for s in posted["volume_anomalies"]] == ["WDC"]
