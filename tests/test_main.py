import os
from unittest.mock import patch
from datetime import datetime, timezone
from main import load_config, run


EMPTY_MARKET = {
    "indices": [], "forex": [], "us_stocks": [],
    "jp_stocks": [], "us_sectors": [], "jp_sectors": [],
}


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


@patch("main.store_report", return_value=True)
@patch("main.post_report", return_value=True)
@patch("main.generate_summary", return_value=None)
@patch("main.parse_forex_factory_events", return_value=[])
@patch("main.collect_news", return_value=[])
@patch("main.get_market_data")
def test_run_stores_to_firestore_when_configured(
    mock_market, mock_news, mock_calendar, mock_summary, mock_post, mock_store
):
    mock_market.return_value = {**EMPTY_MARKET, "timestamp": datetime.now(timezone.utc)}
    with patch.dict(os.environ, {
        "FIREBASE_PROJECT_ID": "test-project",
        "FIREBASE_SERVICE_ACCOUNT": '{"type": "service_account"}',
    }):
        run(webhook_url="https://hooks.slack.com/test", anthropic_api_key="test-key")
    assert mock_store.called
    assert mock_store.call_args.kwargs["project_id"] == "test-project"
    assert mock_store.call_args.kwargs["service_account_info"] == {
        "type": "service_account"
    }


@patch("main.store_report", return_value=True)
@patch("main.post_report", return_value=True)
@patch("main.generate_summary", return_value=None)
@patch("main.parse_forex_factory_events", return_value=[])
@patch("main.collect_news", return_value=[])
@patch("main.get_market_data")
def test_run_skips_firestore_when_not_configured(
    mock_market, mock_news, mock_calendar, mock_summary, mock_post, mock_store
):
    mock_market.return_value = {**EMPTY_MARKET, "timestamp": datetime.now(timezone.utc)}
    env = {k: v for k, v in os.environ.items()
           if k not in ("FIREBASE_PROJECT_ID", "FIREBASE_SERVICE_ACCOUNT")}
    with patch.dict(os.environ, env, clear=True):
        result = run(webhook_url="https://hooks.slack.com/test", anthropic_api_key="test-key")
    assert result is True
    assert not mock_store.called
