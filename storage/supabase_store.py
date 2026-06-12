from __future__ import annotations
import logging

import requests

from collectors.market import PriceData

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SEC = 15

# テーブルごとの upsert 衝突キー（schema.sql の unique 制約と一致させる）
CONFLICT_KEYS = {
    "market_snapshots": "snapshot_date,ticker",
    "news_items": "snapshot_date,url",
    "calendar_events": "snapshot_date,time,currency,title",
    "daily_summaries": "snapshot_date",
}

MARKET_CATEGORIES = {
    "indices": "index",
    "forex": "forex",
    "us_stocks": "us_stock",
    "jp_stocks": "jp_stock",
    "us_sectors": "us_sector",
    "jp_sectors": "jp_sector",
}


def build_rows(data: dict) -> dict[str, list[dict]]:
    market = data["market"]
    snapshot_date = market["timestamp"].strftime("%Y-%m-%d")

    market_rows = []
    for key, category in MARKET_CATEGORIES.items():
        for s in market.get(key, []):
            if not isinstance(s, PriceData):
                continue
            market_rows.append({
                "snapshot_date": snapshot_date,
                "category": category,
                "ticker": s.ticker,
                "name": s.name,
                "price": s.price,
                "change_pct": s.change_pct,
                "volume": s.volume,
                "avg_volume": s.avg_volume,
            })

    news_rows = [
        {
            "snapshot_date": snapshot_date,
            "title": n.title,
            "url": n.url,
            "source": n.source,
            "published": n.published.isoformat(),
            "tickers": n.tickers,
        }
        for n in data.get("news", [])
    ]

    calendar_rows = [
        {
            "snapshot_date": snapshot_date,
            "time": e.time,
            "currency": e.currency,
            "title": e.title,
            "importance": e.importance,
        }
        for e in data.get("calendar", [])
    ]

    summary = data.get("summary")
    summary_rows = []
    if summary is not None:
        summary_rows.append({
            "snapshot_date": snapshot_date,
            "key_points": summary.key_points,
            "mover_explanations": summary.mover_explanations,
        })

    return {
        "market_snapshots": market_rows,
        "news_items": news_rows,
        "calendar_events": calendar_rows,
        "daily_summaries": summary_rows,
    }


def store_report(data: dict, supabase_url: str, service_key: str) -> bool:
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    rows = build_rows(data)
    ok = True
    for table, payload in rows.items():
        if not payload:
            continue
        url = f"{supabase_url}/rest/v1/{table}?on_conflict={CONFLICT_KEYS[table]}"
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SEC
            )
            response.raise_for_status()
            logger.info("Stored %d rows into %s", len(payload), table)
        except Exception as e:
            logger.error("Failed to store rows into %s: %s", table, e)
            ok = False
    return ok
