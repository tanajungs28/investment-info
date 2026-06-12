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


def _mrkdwn_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _news_link(item) -> str:
    title = _mrkdwn_escape(item.title)
    if not item.url:
        return title
    return f"<{item.url}|{title}>"


def _format_index_line(s: PriceData) -> str:
    return f"{s.name:<20} {s.price:>12,.2f}  {_pct_str(s.change_pct)} {_arrow(s.change_pct)}"


SECTOR_BAR_WIDTH = 8


def _format_sector_bars(sectors: list[PriceData], bar_width: int = SECTOR_BAR_WIDTH) -> str:
    ranked = sorted(sectors, key=lambda s: s.change_pct, reverse=True)
    max_abs = max((abs(s.change_pct) for s in ranked), default=0) or 1.0
    lines = []
    for s in ranked:
        length = round(abs(s.change_pct) / max_abs * bar_width)
        if s.change_pct != 0:
            length = max(1, length)
        bar = ("█" if s.change_pct >= 0 else "▒") * length
        lines.append(f"{s.name:<16} {_pct_str(s.change_pct):>7} {bar}")
    return "\n".join(lines)


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
                "text": "📈 *セクター動向（米国）*\n```\n"
                + _format_sector_bars(market["us_sectors"]) + "\n```",
            },
        })

    if market.get("jp_sectors"):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📈 *セクター動向（日本）*\n```\n"
                + _format_sector_bars(market["jp_sectors"]) + "\n```",
            },
        })

    blocks.append({"type": "divider"})

    anomalies: list[PriceData] = data.get("volume_anomalies", [])
    if anomalies:
        anomaly_lines = [
            f"{s.ticker:<12} {s.name:<16} 通常比 {s.volume_ratio:.1f}倍  "
            f"({_pct_str(s.change_pct)} {_arrow(s.change_pct)})"
            for s in anomalies[:8]
        ]
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⚡ *出来高急増アラート*\n```\n" + "\n".join(anomaly_lines) + "\n```",
            },
        })
        blocks.append({"type": "divider"})

    mover_explanations: dict[str, str] = summary.mover_explanations if summary else {}

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
            ratio = s.volume_ratio
            if ratio is not None and ratio >= 1.5:
                line += f"  出来高 {ratio:.1f}倍"
            mover_lines.append(line)
            explanation = mover_explanations.get(s.ticker)
            if explanation:
                mover_lines.append(f"  └ {explanation}")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🔍 *ウォッチ銘柄ハイライト*\n```\n" + "\n".join(mover_lines) + "\n```",
            },
        })
        blocks.append({"type": "divider"})

    from collectors.news import NewsItem as _NewsItem

    ticker_news: dict[str, list[_NewsItem]] = {}
    general_news: list[_NewsItem] = []
    for item in news_items:
        if item.tickers:
            for ticker in item.tickers:
                ticker_news.setdefault(ticker, []).append(item)
        else:
            general_news.append(item)

    if ticker_news or general_news:
        news_lines = []
        for ticker, items_for_ticker in list(ticker_news.items())[:12]:
            for item in items_for_ticker[:3]:
                news_lines.append(f"[{ticker}] {_news_link(item)}  _({item.source})_")
        for item in general_news[:5]:
            news_lines.append(f"[市場全般] {_news_link(item)}  _({item.source})_")
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
