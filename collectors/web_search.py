from __future__ import annotations
from datetime import datetime, timedelta, timezone
import calendar
import html
import logging
import urllib.parse

import feedparser

from collectors.market import PriceData
from collectors.news import NewsItem

logger = logging.getLogger(__name__)

_GOOGLE_NEWS_BASE = "https://news.google.com/rss/search"


def search_google_news(
    query: str,
    lang: str = "en",
    max_results: int = 5,
    lookback_hours: int = 48,
) -> list[NewsItem]:
    if lang == "ja":
        params = f"?q={urllib.parse.quote(query)}&hl=ja&gl=JP&ceid=JP:ja"
        source = "Google ニュース"
    else:
        params = f"?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        source = "Google News"

    url = _GOOGLE_NEWS_BASE + params
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    try:
        feed = feedparser.parse(url)
        items: list[NewsItem] = []
        for entry in feed.entries[:max_results]:
            try:
                published = datetime.fromtimestamp(
                    calendar.timegm(entry.published_parsed), tz=timezone.utc
                )
            except Exception:
                published = datetime.now(timezone.utc)
            if published < cutoff:
                continue
            items.append(
                NewsItem(
                    title=html.unescape(getattr(entry, "title", "")),
                    url=getattr(entry, "link", ""),
                    source=source,
                    published=published,
                )
            )
        return items
    except Exception as e:
        logger.warning("Google News search failed for '%s': %s", query, e)
        return []


def fetch_mover_news(
    movers: list[PriceData],
    results_per_stock: int = 5,
    lookback_hours: int = 48,
) -> dict[str, list[NewsItem]]:
    result: dict[str, list[NewsItem]] = {}
    for stock in movers:
        ticker_bare = stock.ticker.replace(".T", "")
        is_jp = stock.ticker.endswith(".T")

        if is_jp:
            query = f"{stock.name} 株価 決算 材料"
            items = search_google_news(
                query, lang="ja", max_results=results_per_stock, lookback_hours=lookback_hours
            )
        else:
            query = f"{ticker_bare} {stock.name} stock"
            items = search_google_news(
                query, lang="en", max_results=results_per_stock, lookback_hours=lookback_hours
            )

        for item in items:
            item.tickers = [stock.ticker]

        result[stock.ticker] = items
        logger.info("Fetched %d web news items for %s", len(items), stock.ticker)

    return result
