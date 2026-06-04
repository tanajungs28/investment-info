from __future__ import annotations
import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from collectors.market import get_market_data
from collectors.news import collect_news
from collectors.calendar import parse_forex_factory_events
from reporters.claude_client import generate_summary
from reporters.slack import post_report

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/error.log"),
    ],
)
logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent / "config"


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

    logger.info("Generating Claude summary...")
    summary = generate_summary(
        news_items=news,
        market_data=market,
        api_key=anthropic_api_key,
        model=st["claude"]["model"],
    )

    logger.info("Posting to Slack...")
    result = post_report(
        data={"market": market, "news": news, "calendar": calendar, "summary": summary},
        webhook_url=webhook_url,
    )

    if result:
        logger.info("Report posted successfully.")
    else:
        logger.error("Failed to post report to Slack.")
    return result


if __name__ == "__main__":
    webhook = os.environ["SLACK_WEBHOOK_URL"]
    api_key = os.environ["ANTHROPIC_API_KEY"]
    run(webhook_url=webhook, anthropic_api_key=api_key)
