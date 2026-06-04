from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import calendar
import logging

import feedparser

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published: datetime
    tickers: list[str] = field(default_factory=list)


def fetch_rss_news(
    url: str, source_name: str, lookback_hours: int = 24
) -> list[NewsItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries:
            try:
                published = datetime.fromtimestamp(
                    calendar.timegm(entry.published_parsed), tz=timezone.utc
                )
            except Exception:
                continue
            if published < cutoff:
                continue
            items.append(
                NewsItem(
                    title=entry.title,
                    url=entry.link,
                    source=source_name,
                    published=published,
                )
            )
        return items
    except Exception as e:
        logger.warning("Failed to fetch RSS from %s: %s", url, e)
        return []


def match_tickers(items: list[NewsItem], watchlist: list[dict]) -> list[NewsItem]:
    for item in items:
        for stock in watchlist:
            ticker_bare = stock["ticker"].replace(".T", "")
            name = stock["name"]
            title_upper = item.title.upper()
            if ticker_bare.upper() in title_upper or name in item.title:
                if stock["ticker"] not in item.tickers:
                    item.tickers.append(stock["ticker"])
    return items


def collect_news(
    rss_feeds: list[dict],
    all_stocks: list[dict],
    lookback_hours: int = 24,
) -> list[NewsItem]:
    items: list[NewsItem] = []
    for feed in rss_feeds:
        fetched = fetch_rss_news(feed["url"], feed["name"], lookback_hours)
        items.extend(fetched)
    items = match_tickers(items, all_stocks)
    items.sort(key=lambda x: x.published, reverse=True)
    return items
