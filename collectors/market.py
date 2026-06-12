from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import logging
import time

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    ticker: str
    name: str
    price: float
    change_pct: float
    volume: int | None = None
    avg_volume: int | None = None

    @property
    def volume_ratio(self) -> float | None:
        if not self.volume or not self.avg_volume:
            return None
        return round(self.volume / self.avg_volume, 2)


def detect_volume_anomalies(
    stocks: list[PriceData], threshold: float = 2.0
) -> list[PriceData]:
    flagged = [
        s for s in stocks
        if s.volume_ratio is not None and s.volume_ratio >= threshold
    ]
    return sorted(flagged, key=lambda s: s.volume_ratio, reverse=True)


def get_price_data(ticker: str, name: str, retries: int = 3) -> PriceData | None:
    for attempt in range(retries):
        try:
            t = yf.Ticker(ticker)
            price = t.fast_info.last_price
            prev_close = t.fast_info.previous_close
            if price is None or prev_close is None:
                return None
            change_pct = (price - prev_close) / prev_close * 100
            volume = t.info.get("regularMarketVolume")
            avg_volume = t.fast_info.three_month_average_volume
            return PriceData(
                ticker=ticker,
                name=name,
                price=round(price, 2),
                change_pct=round(change_pct, 2),
                volume=volume,
                avg_volume=int(avg_volume) if avg_volume else None,
            )
        except Exception as e:
            logger.warning("Attempt %d failed for %s: %s", attempt + 1, ticker, e)
            if attempt < retries - 1:
                time.sleep(1)
    return None


def get_market_data(
    indices: list[dict],
    forex: list[dict],
    us_stocks: list[dict],
    jp_stocks: list[dict],
    us_sectors: list[dict],
    jp_sectors: list[dict],
) -> dict:
    def fetch_list(items: list[dict]) -> list[PriceData]:
        results = []
        for item in items:
            data = get_price_data(item["ticker"], item["name"])
            if data:
                results.append(data)
        return results

    return {
        "indices": fetch_list(indices),
        "forex": fetch_list(forex),
        "us_stocks": fetch_list(us_stocks),
        "jp_stocks": fetch_list(jp_stocks),
        "us_sectors": fetch_list(us_sectors),
        "jp_sectors": fetch_list(jp_sectors),
        "timestamp": datetime.now(),
    }
