from unittest.mock import MagicMock, patch
from collectors.market import (
    get_price_data,
    get_market_data,
    detect_volume_anomalies,
    PriceData,
)


def make_mock_ticker(price=100.0, prev_close=98.0, volume=1000000, avg_volume=900000):
    ticker = MagicMock()
    ticker.fast_info.last_price = price
    ticker.fast_info.previous_close = prev_close
    ticker.fast_info.three_month_average_volume = avg_volume
    ticker.info = {"regularMarketVolume": volume}
    return ticker


@patch("collectors.market.yf.Ticker")
def test_get_price_data_returns_price_data(mock_ticker_cls):
    mock_ticker_cls.return_value = make_mock_ticker(price=150.0, prev_close=145.0)
    result = get_price_data("AAPL", "Apple")
    assert isinstance(result, PriceData)
    assert result.ticker == "AAPL"
    assert result.name == "Apple"
    assert result.price == 150.0
    assert abs(result.change_pct - 3.45) < 0.1


@patch("collectors.market.yf.Ticker")
def test_get_price_data_returns_none_on_missing_price(mock_ticker_cls):
    mock_ticker_cls.return_value.fast_info.last_price = None
    result = get_price_data("INVALID", "Invalid")
    assert result is None


@patch("collectors.market.get_price_data")
def test_get_market_data_returns_all_sections(mock_get_price):
    mock_get_price.return_value = PriceData(
        ticker="TEST", name="Test", price=100.0, change_pct=1.0
    )
    data = get_market_data(
        indices=[{"ticker": "^GSPC", "name": "S&P 500"}],
        forex=[],
        us_stocks=[],
        jp_stocks=[],
        us_sectors=[],
        jp_sectors=[],
    )
    assert "indices" in data
    assert "us_stocks" in data
    assert "timestamp" in data
    assert len(data["indices"]) == 1
    assert data["indices"][0].ticker == "TEST"


def test_volume_ratio_is_computed_from_volume_and_average():
    s = PriceData("NVDA", "NVIDIA", 100.0, 1.0, volume=60_000_000, avg_volume=30_000_000)
    assert s.volume_ratio == 2.0


def test_volume_ratio_is_none_when_volume_missing():
    s = PriceData("NVDA", "NVIDIA", 100.0, 1.0)
    assert s.volume_ratio is None


def test_volume_ratio_is_none_when_avg_volume_zero():
    s = PriceData("NVDA", "NVIDIA", 100.0, 1.0, volume=100, avg_volume=0)
    assert s.volume_ratio is None


def test_detect_volume_anomalies_filters_by_threshold_and_sorts_desc():
    quiet = PriceData("AAPL", "Apple", 100.0, 0.1, volume=10, avg_volume=10)
    spike = PriceData("MU", "Micron", 100.0, 0.2, volume=30, avg_volume=10)
    bigger = PriceData("WDC", "Western Digital", 100.0, 0.3, volume=50, avg_volume=10)
    result = detect_volume_anomalies([quiet, spike, bigger], threshold=2.0)
    assert [s.ticker for s in result] == ["WDC", "MU"]


def test_detect_volume_anomalies_skips_stocks_without_volume_data():
    s = PriceData("X", "NoVolume", 100.0, 0.0)
    assert detect_volume_anomalies([s]) == []
