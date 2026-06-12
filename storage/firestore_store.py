from __future__ import annotations
import logging

import requests

from collectors.market import PriceData

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SEC = 15
FIRESTORE_SCOPE = "https://www.googleapis.com/auth/datastore"

MARKET_CATEGORIES = {
    "indices": "index",
    "forex": "forex",
    "us_stocks": "us_stock",
    "jp_stocks": "jp_stock",
    "us_sectors": "us_sector",
    "jp_sectors": "jp_sector",
}


def build_report_doc(data: dict) -> dict:
    """レポートデータを Firestore の1日1ドキュメント形式に変換する。"""
    market = data["market"]
    snapshot_date = market["timestamp"].strftime("%Y-%m-%d")

    market_rows = []
    for key, category in MARKET_CATEGORIES.items():
        for s in market.get(key, []):
            if not isinstance(s, PriceData):
                continue
            market_rows.append({
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
            "time": e.time,
            "currency": e.currency,
            "title": e.title,
            "importance": e.importance,
        }
        for e in data.get("calendar", [])
    ]

    summary = data.get("summary")
    summary_doc = None
    if summary is not None:
        summary_doc = {
            "key_points": summary.key_points,
            "mover_explanations": summary.mover_explanations,
        }

    return {
        "snapshot_date": snapshot_date,
        "market": market_rows,
        "news": news_rows,
        "calendar": calendar_rows,
        "summary": summary_doc,
    }


def _fs_value(v) -> dict:
    if v is None:
        return {"nullValue": None}
    if isinstance(v, bool):
        return {"booleanValue": v}
    if isinstance(v, int):
        return {"integerValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    if isinstance(v, str):
        return {"stringValue": v}
    if isinstance(v, list):
        return {"arrayValue": {"values": [_fs_value(x) for x in v]}}
    if isinstance(v, dict):
        return {"mapValue": {"fields": {k: _fs_value(x) for k, x in v.items()}}}
    raise TypeError(f"Unsupported Firestore value type: {type(v)}")


def to_firestore_fields(doc: dict) -> dict:
    return {k: _fs_value(v) for k, v in doc.items()}


def _get_access_token(service_account_info: dict) -> str:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request

    creds = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=[FIRESTORE_SCOPE]
    )
    creds.refresh(Request())
    return creds.token


def store_report(data: dict, project_id: str, service_account_info: dict) -> bool:
    doc = build_report_doc(data)
    url = (
        f"https://firestore.googleapis.com/v1/projects/{project_id}"
        f"/databases/(default)/documents/daily_reports/{doc['snapshot_date']}"
    )
    try:
        token = _get_access_token(service_account_info)
        response = requests.patch(
            url,
            json={"fields": to_firestore_fields(doc)},
            headers={"Authorization": f"Bearer {token}"},
            timeout=REQUEST_TIMEOUT_SEC,
        )
        response.raise_for_status()
        logger.info(
            "Stored daily report %s to Firestore (%d market rows, %d news)",
            doc["snapshot_date"], len(doc["market"]), len(doc["news"]),
        )
        return True
    except Exception as e:
        logger.error("Failed to store report to Firestore: %s", e)
        return False
