from datetime import datetime, timezone

import responses as resp_module

from storage.supabase_store import build_rows, store_report
from collectors.market import PriceData
from collectors.news import NewsItem
from collectors.calendar import EconomicEvent
from reporters.claude_client import SummaryResult

SUPABASE_URL = "https://test-project.supabase.co"
SERVICE_KEY = "service-role-test-key"


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


def test_build_rows_tags_market_rows_with_category_and_date():
    rows = build_rows(make_data())
    market_rows = rows["market_snapshots"]
    assert all(r["snapshot_date"] == "2026-06-12" for r in market_rows)
    categories = {r["ticker"]: r["category"] for r in market_rows}
    assert categories["NVDA"] == "us_stock"
    assert categories["7203.T"] == "jp_stock"
    assert categories["XLK"] == "us_sector"
    assert categories["^GSPC"] == "index"
    assert categories["JPY=X"] == "forex"


def test_build_rows_includes_volume_fields():
    rows = build_rows(make_data())
    nvda = next(r for r in rows["market_snapshots"] if r["ticker"] == "NVDA")
    assert nvda["volume"] == 50_000_000
    assert nvda["avg_volume"] == 30_000_000


def test_build_rows_serializes_news_with_tickers_and_iso_date():
    rows = build_rows(make_data())
    news = rows["news_items"]
    assert len(news) == 1
    assert news[0]["tickers"] == ["NVDA"]
    assert news[0]["published"].startswith("2026-06-12T01:00")


def test_build_rows_serializes_summary_and_calendar():
    rows = build_rows(make_data())
    assert rows["daily_summaries"][0]["key_points"] == ["① CPIに注目"]
    assert rows["daily_summaries"][0]["mover_explanations"] == {"NVDA": "新型GPU発表で上昇。"}
    assert rows["calendar_events"][0]["title"] == "CPI (MoM)"
    assert rows["calendar_events"][0]["importance"] == 3


def test_build_rows_skips_summary_when_none():
    data = make_data()
    data["summary"] = None
    rows = build_rows(data)
    assert rows["daily_summaries"] == []


@resp_module.activate
def test_store_report_posts_to_all_tables_with_auth_headers():
    for table in ["market_snapshots", "news_items", "calendar_events", "daily_summaries"]:
        resp_module.add(
            resp_module.POST, f"{SUPABASE_URL}/rest/v1/{table}", status=201
        )
    result = store_report(make_data(), SUPABASE_URL, SERVICE_KEY)
    assert result is True
    assert len(resp_module.calls) == 4
    first = resp_module.calls[0].request
    assert first.headers["apikey"] == SERVICE_KEY
    assert first.headers["Authorization"] == f"Bearer {SERVICE_KEY}"
    assert "resolution=merge-duplicates" in first.headers["Prefer"]


@resp_module.activate
def test_store_report_returns_false_but_continues_on_table_error():
    resp_module.add(
        resp_module.POST, f"{SUPABASE_URL}/rest/v1/market_snapshots", status=500
    )
    for table in ["news_items", "calendar_events", "daily_summaries"]:
        resp_module.add(
            resp_module.POST, f"{SUPABASE_URL}/rest/v1/{table}", status=201
        )
    result = store_report(make_data(), SUPABASE_URL, SERVICE_KEY)
    assert result is False
    assert len(resp_module.calls) == 4
