from datetime import datetime, timezone
import responses as resp_module
from reporters.slack import post_report, build_report_blocks
from collectors.market import PriceData
from collectors.news import NewsItem
from collectors.calendar import EconomicEvent
from reporters.claude_client import SummaryResult


def make_report_data() -> dict:
    return {
        "market": {
            "indices": [PriceData("^GSPC", "S&P 500", 5234.0, 0.82)],
            "forex": [PriceData("JPY=X", "USD/JPY", 157.23, 0.1)],
            "us_stocks": [
                PriceData("NVDA", "NVIDIA", 892.0, 3.21, volume=50_000_000, avg_volume=30_000_000)
            ],
            "jp_stocks": [PriceData("7203.T", "トヨタ自動車", 3250.0, 1.5)],
            "us_sectors": [
                PriceData("XLK", "テクノロジー", 210.0, 1.4),
                PriceData("XLE", "エネルギー", 88.0, -0.8),
            ],
            "jp_sectors": [],
            "timestamp": datetime(2025, 6, 4, 6, 0, 0, tzinfo=timezone.utc),
        },
        "news": [
            NewsItem(
                title="NVIDIAが新型GPU発表",
                url="http://example.com",
                source="株探",
                published=datetime.now(timezone.utc),
                tickers=["NVDA"],
            )
        ],
        "calendar": [EconomicEvent("22:30", "USD", "CPI (MoM)", 3)],
        "summary": SummaryResult(
            key_points=["① CPIに注目", "② NVDAモメンタム", "③ 円安一服"],
            mover_explanations={"NVDA": "新型GPU発表を受けて買いが集まり上昇。"},
        ),
    }


def test_build_report_blocks_returns_non_empty_list():
    blocks = build_report_blocks(make_report_data())
    assert isinstance(blocks, list)
    assert len(blocks) > 0


def test_build_report_blocks_contains_sp500():
    blocks = build_report_blocks(make_report_data())
    all_text = " ".join(str(b.get("text", {}).get("text", "")) for b in blocks)
    assert "S&P 500" in all_text


def test_build_report_blocks_shows_mover_explanation():
    blocks = build_report_blocks(make_report_data())
    all_text = " ".join(str(b.get("text", {}).get("text", "")) for b in blocks)
    assert "新型GPU発表" in all_text


def test_build_report_blocks_shows_news_source():
    blocks = build_report_blocks(make_report_data())
    all_text = " ".join(str(b.get("text", {}).get("text", "")) for b in blocks)
    assert "株探" in all_text


def test_build_report_blocks_contains_claude_summary():
    blocks = build_report_blocks(make_report_data())
    all_text = " ".join(str(b.get("text", {}).get("text", "")) for b in blocks)
    assert "CPIに注目" in all_text


@resp_module.activate
def test_post_report_returns_true_on_success():
    webhook_url = "https://hooks.slack.com/services/TEST"
    resp_module.add(resp_module.POST, webhook_url, json={"ok": True}, status=200)
    assert post_report(make_report_data(), webhook_url) is True


@resp_module.activate
def test_post_report_returns_false_on_http_error():
    webhook_url = "https://hooks.slack.com/services/TEST"
    resp_module.add(resp_module.POST, webhook_url, status=500)
    assert post_report(make_report_data(), webhook_url) is False
