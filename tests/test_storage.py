from datetime import datetime, timezone
from unittest.mock import patch

import responses as resp_module

from storage.firestore_store import build_report_doc, to_firestore_fields, store_report
from collectors.market import PriceData
from collectors.news import NewsItem
from collectors.calendar import EconomicEvent
from reporters.claude_client import SummaryResult

PROJECT_ID = "test-project"
DOC_URL = (
    "https://firestore.googleapis.com/v1/projects/test-project"
    "/databases/(default)/documents/daily_reports/2026-06-12"
)


def make_data() -> dict:
    return {
        "market": {
            "indices": [PriceData("^GSPC", "S&P 500", 5234.0, 0.82)],
            "forex": [PriceData("JPY=X", "USD/JPY", 157.23, 0.1)],
            "us_stocks": [
                PriceData("NVDA", "NVIDIA", 892.0, 3.21,
                          volume=50_000_000, avg_volume=30_000_000)
            ],
            "jp_stocks": [PriceData("7203.T", "トヨタ自動車", 3250.0, 1.5)],
            "us_sectors": [PriceData("XLK", "テクノロジー", 210.0, 1.4)],
            "jp_sectors": [],
            "timestamp": datetime(2026, 6, 12, 6, 0, 0),
        },
        "news": [
            NewsItem(
                title="NVIDIAが新型GPU発表",
                url="http://example.com/gpu",
                source="日経 マーケット",
                published=datetime(2026, 6, 12, 1, 0, tzinfo=timezone.utc),
                tickers=["NVDA"],
            )
        ],
        "calendar": [EconomicEvent("22:30", "USD", "CPI (MoM)", 3)],
        "summary": SummaryResult(
            key_points=["① CPIに注目"],
            mover_explanations={"NVDA": "新型GPU発表で上昇。"},
        ),
    }


def test_build_report_doc_has_date_and_categorized_market_rows():
    doc = build_report_doc(make_data())
    assert doc["snapshot_date"] == "2026-06-12"
    categories = {r["ticker"]: r["category"] for r in doc["market"]}
    assert categories["NVDA"] == "us_stock"
    assert categories["7203.T"] == "jp_stock"
    assert categories["XLK"] == "us_sector"
    assert categories["^GSPC"] == "index"
    assert categories["JPY=X"] == "forex"


def test_build_report_doc_serializes_news_and_summary():
    doc = build_report_doc(make_data())
    assert doc["news"][0]["tickers"] == ["NVDA"]
    assert doc["news"][0]["published"].startswith("2026-06-12T01:00")
    assert doc["summary"]["key_points"] == ["① CPIに注目"]
    assert doc["calendar"][0]["importance"] == 3


def test_build_report_doc_summary_none():
    data = make_data()
    data["summary"] = None
    doc = build_report_doc(data)
    assert doc["summary"] is None


def test_to_firestore_fields_encodes_all_types():
    fields = to_firestore_fields({
        "s": "text",
        "i": 42,
        "f": 1.5,
        "b": True,
        "n": None,
        "arr": ["a", 1],
        "map": {"k": "v"},
    })
    assert fields["s"] == {"stringValue": "text"}
    assert fields["i"] == {"integerValue": "42"}
    assert fields["f"] == {"doubleValue": 1.5}
    assert fields["b"] == {"booleanValue": True}
    assert fields["n"] == {"nullValue": None}
    assert fields["arr"]["arrayValue"]["values"][0] == {"stringValue": "a"}
    assert fields["map"]["mapValue"]["fields"]["k"] == {"stringValue": "v"}


@resp_module.activate
@patch("storage.firestore_store._get_access_token", return_value="test-token")
def test_store_report_patches_daily_report_document(mock_token):
    resp_module.add(resp_module.PATCH, DOC_URL, json={"name": "ok"}, status=200)
    result = store_report(make_data(), project_id=PROJECT_ID, service_account_info={})
    assert result is True
    req = resp_module.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert '"snapshot_date"' in req.body if isinstance(req.body, str) else b'"snapshot_date"' in req.body


@resp_module.activate
@patch("storage.firestore_store._get_access_token", return_value="test-token")
def test_store_report_returns_false_on_http_error(mock_token):
    resp_module.add(resp_module.PATCH, DOC_URL, status=403)
    result = store_report(make_data(), project_id=PROJECT_ID, service_account_info={})
    assert result is False


@patch("storage.firestore_store._get_access_token", side_effect=ValueError("bad key"))
def test_store_report_returns_false_on_auth_error(mock_token):
    result = store_report(make_data(), project_id=PROJECT_ID, service_account_info={})
    assert result is False
