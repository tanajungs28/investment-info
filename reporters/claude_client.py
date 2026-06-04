from __future__ import annotations
from dataclasses import dataclass, field
import logging

import anthropic

from collectors.news import NewsItem
from collectors.market import PriceData

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    key_points: list[str]
    mover_explanations: dict[str, str] = field(default_factory=dict)


def _build_prompt(news_items: list[NewsItem], market_data: dict) -> str:
    news_lines = []
    for item in news_items[:40]:
        tickers = ", ".join(item.tickers) if item.tickers else "市場全般"
        news_lines.append(f"[{tickers}] {item.title}")

    movers: list[PriceData] = []
    for stock in market_data.get("us_stocks", []) + market_data.get("jp_stocks", []):
        if isinstance(stock, PriceData) and abs(stock.change_pct) >= 1.0:
            movers.append(stock)
    movers.sort(key=lambda s: abs(s.change_pct), reverse=True)

    mover_lines = []
    for s in movers:
        direction = "▲" if s.change_pct > 0 else "▼"
        mover_lines.append(f"{s.ticker} ({s.name}) {direction}{abs(s.change_pct):.1f}%")

    news_text = "\n".join(news_lines) if news_lines else "ニュースなし"
    movers_text = "\n".join(mover_lines) if mover_lines else "なし"
    mover_tickers = [s.ticker for s in movers] if movers else []

    explanation_section = ""
    if mover_tickers:
        ticker_list = "\n".join(f"- {t}" for t in mover_tickers)
        explanation_section = f"""
【値動きの背景】セクションでは、以下の各銘柄について値動きの理由をニュースから読み取り1〜2文で説明してください：
{ticker_list}

"""

    return f"""以下は本日の株式市場のニュースと値動きです。

## 直近ニュース
{news_text}

## 主な値動き（±1%以上）
{movers_text}

上記をもとに、以下の形式で回答してください。

【値動きの背景】
{explanation_section}（各銘柄コード）: （ニュースに基づく値動きの理由を1〜2文で。該当ニュースがなければ「関連ニュースなし」）

【今日の注目ポイント】
① （ポイント1を1〜2文で）
② （ポイント2を1〜2文で）
③ （ポイント3を1〜2文で）"""


def _parse_response(text: str, market_data: dict) -> SummaryResult:
    mover_tickers = set()
    for stock in market_data.get("us_stocks", []) + market_data.get("jp_stocks", []):
        if isinstance(stock, PriceData) and abs(stock.change_pct) >= 1.0:
            mover_tickers.add(stock.ticker)

    mover_explanations: dict[str, str] = {}
    key_points: list[str] = []

    in_background = False
    in_points = False

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if "【値動きの背景】" in stripped:
            in_background = True
            in_points = False
            continue
        if "【今日の注目ポイント】" in stripped:
            in_background = False
            in_points = True
            continue
        if in_background and ":" in stripped:
            ticker, _, explanation = stripped.partition(":")
            ticker = ticker.strip()
            if ticker in mover_tickers:
                mover_explanations[ticker] = explanation.strip()
        elif in_points and stripped and stripped[0] in "①②③":
            key_points.append(stripped)

    if not key_points:
        key_points = [l.strip() for l in text.split("\n") if l.strip()]

    return SummaryResult(key_points=key_points, mover_explanations=mover_explanations)


def generate_summary(
    news_items: list[NewsItem],
    market_data: dict,
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
) -> SummaryResult | None:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = _build_prompt(news_items, market_data)
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        return _parse_response(text, market_data)
    except Exception as e:
        logger.error("Claude API error: %s", e)
        return None
