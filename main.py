from __future__ import annotations
import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from collectors.market import get_market_data, detect_volume_anomalies, PriceData
from collectors.news import collect_news
from collectors.calendar import parse_forex_factory_events
from collectors.web_search import fetch_mover_news
from reporters.claude_client import generate_summary
from reporters.slack import post_report
from storage.supabase_store import store_report

load_dotenv()

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "error.log"),
    ],
)
logger = logging.getLogger(__name__)

CONFIG_DIR = BASE_DIR / "config"


def load_config() -> dict:
    with open(CONFIG_DIR / "watchlist.yaml", encoding="utf-8") as f:
        watchlist = yaml.safe_load(f)
    with open(CONFIG_DIR / "settings.yaml", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    return {"watchlist": watchlist, "settings": settings}


def run(webhook_url: str, anthropic_api_key: str) -> bool:
    config = load_config()
    wl = config["watchlist"]
    st = config["settings"]

    all_stocks = wl["stocks"]["us"] + wl["stocks"]["jp"]

    logger.info("Collecting market data...")
    market = get_market_data(
        indices=wl["indices"]["us"] + wl["indices"]["jp"],
        forex=wl["forex"],
        us_stocks=wl["stocks"]["us"],
        jp_stocks=wl["stocks"]["jp"],
        us_sectors=wl["sectors"]["us"],
        jp_sectors=wl["sectors"]["jp"],
    )

    logger.info("Collecting news...")
    news = collect_news(
        rss_feeds=st["news"]["rss_feeds"]["jp"],
        all_stocks=all_stocks,
        lookback_hours=st["news"]["lookback_hours"],
    )

    logger.info("Collecting economic calendar...")
    calendar = parse_forex_factory_events(
        url=st["calendar"]["forex_factory_rss"],
        min_importance=st["calendar"]["min_importance"],
    )

    logger.info("Fetching web news for notable movers...")
    all_stocks_data: list[PriceData] = market.get("us_stocks", []) + market.get("jp_stocks", [])
    movers = [s for s in all_stocks_data if isinstance(s, PriceData) and abs(s.change_pct) >= 1.0]
    mover_news = fetch_mover_news(movers) if movers else {}

    logger.info("Detecting volume anomalies...")
    spike_ratio = st.get("alerts", {}).get("volume_spike_ratio", 2.0)
    anomalies = detect_volume_anomalies(all_stocks_data, threshold=spike_ratio)

    logger.info("Generating Claude summary...")
    summary = generate_summary(
        news_items=news,
        market_data=market,
        api_key=anthropic_api_key,
        model=st["claude"]["model"],
        mover_news=mover_news,
    )

    report_data = {
        "market": market,
        "news": news,
        "calendar": calendar,
        "summary": summary,
        "volume_anomalies": anomalies,
    }

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        logger.info("Storing report data to Supabase...")
        # 永続化の失敗でレポート投稿は止めない
        store_report(report_data, supabase_url=supabase_url, service_key=supabase_key)
    else:
        logger.info("Supabase not configured; skipping persistence.")

    logger.info("Posting to Slack...")
    result = post_report(data=report_data, webhook_url=webhook_url)

    if result:
        logger.info("Report posted successfully.")
    else:
        logger.error("Failed to post report to Slack.")
    return result


if __name__ == "__main__":
    import sys
    webhook = os.environ["SLACK_WEBHOOK_URL"]
    api_key = os.environ["ANTHROPIC_API_KEY"]
    success = run(webhook_url=webhook, anthropic_api_key=api_key)
    sys.exit(0 if success else 1)
