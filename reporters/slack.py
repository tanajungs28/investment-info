from __future__ import annotations
import logging

import requests

from collectors.market import PriceData

logger = logging.getLogger(__name__)


def _arrow(change_pct: float) -> str:
    if change_pct > 0.05:
        return "▲"
    if change_pct < -0.05:
        return "▼"
    return "─"


def _pct_str(change_pct: float) -> str:
    sign = "+" if change_pct > 0 else ""
    return f"{sign}{change_pct:.2f}%"


def _format_index_line(s: PriceData) -> str:
    return f"{s.name:<20} {s.price:>12,.2f}  {_pct_str(s.change_pct)} {_arrow(s.change_pct)}"


def _format_sector_summary(sectors: list[PriceData], top_n: int = 3) -> str:
    if not sectors:
        return "データなし"
    ranked = sorted(sectors, key=lambda s: s.change_pct, reverse=True)
    top = " / ".join(
        f"{s.name} {_pct_str(s.change_pct)}" for s in ranked[:top_n]
    )
    bottom = " / ".join(
        f"{s.name} {_pct_str(s.change_pct)}" for s in ranked[-top_n:]
    )
    return f"上位: {top}\n  下位: {bottom}"


def build_report_blocks(data: dict) -> list[dict]:
    market = data["market"]
    news_items = data.get("news", [])
    calendar = data.get("calendar", [])
    summary = data.get("summary")
    timestamp = market["timestamp"]
    date_str = timestamp.strftime("%Y-%m-%d (%a)")

    blocks: list[dict] = []

    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"📊 モーニングレポート  {date_str} 06:00 JST"},
    })
    blocks.append({"type": "divider"})

    index_lines = [_format_index_line(s) for s in market["indices"]]
    forex_lines = [f"{s.name:<20} {s.price:>12.2f}" for s in market["forex"]]
    market_text = "```\n" + "\n".join(index_lines + [""] + forex_lines) + "\n```"
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": market_text}})

    if calendar:
        star = {3: "★★★", 2: "★★☆", 1: "★☆☆"}
        cal_lines = [
            f"  {e.time} {e.currency}  {star.get(e.importance, '')}  {e.title}"
            for e in calendar[:6]
        ]
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "🗓 *本日の経済指標*\n" + "\n".join(cal_lines)},
        })
        blocks.append({"type": "divider"})

    if market.get("us_sectors"):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📈 *セクター動向（米国）*\n  " + _format_sector_summary(market["us_sectors"]),
            },
        })

    if market.get("jp_sectors"):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📈 *セクター動向（日本）*\n  " + _format_sector_summary(market["jp_sectors"]),
            },
        })

    blocks.append({"type": "divider"})

    all_stocks: list[PriceData] = market.get("us_stocks", []) + market.get("jp_stocks", [])
    movers = sorted(
        [s for s in all_stocks if abs(s.change_pct) >= 1.0],
        key=lambda s: abs(s.change_pct),
        reverse=True,
    )
    if movers:
        mover_lines = []
        for s in movers[:10]:
            line = f"{s.ticker:<12} {s.name:<16} {s.price:>10,.2f}  {_pct_str(s.change_pct)} {_arrow(s.change_pct)}"
            if s.volume and s.avg_volume and s.avg_volume > 0:
                ratio = s.volume / s.avg_volume
                if ratio >= 1.5:
                    line += f"  出来高 {ratio:.1f}倍"
            mover_lines.append(line)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🔍 *ウォッチ銘柄ハイライト*\n```\n" + "\n".join(mover_lines) + "\n```",
            },
        })
        blocks.append({"type": "divider"})

    ticker_news: dict[str, list[str]] = {}
    for item in news_items:
        for ticker in item.tickers:
            ticker_news.setdefault(ticker, []).append(item.title)
    if ticker_news:
        news_lines = []
        for ticker, titles in list(ticker_news.items())[:8]:
            for title in titles[:2]:
                news_lines.append(f"[{ticker}] {title}")
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "📰 *注目ニュース*\n" + "\n".join(news_lines)},
        })
        blocks.append({"type": "divider"})

    if summary and summary.key_points:
        points_text = "\n".join(summary.key_points[:3])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"💡 *今日の注目ポイント（Claude）*\n{points_text}"},
        })

    return blocks


def post_report(data: dict, webhook_url: str) -> bool:
    blocks = build_report_blocks(data)
    try:
        response = requests.post(webhook_url, json={"blocks": blocks}, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error("Slack post failed: %s", e)
        return False
