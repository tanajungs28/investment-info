from __future__ import annotations
from dataclasses import dataclass
import logging

import anthropic

from collectors.news import NewsItem
from collectors.market import PriceData

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    key_points: list[str]


def _build_prompt(news_items: list[NewsItem], market_data: dict) -> str:
    news_lines = []
    for item in news_items[:20]:
        tickers = ", ".join(item.tickers) if item.tickers else "市場全般"
        news_lines.append(f"[{tickers}] {item.title}")

    movers = []
    for stock in market_data.get("us_stocks", []) + market_data.get("jp_stocks", []):
        if isinstance(stock, PriceData) and abs(stock.change_pct) >= 1.0:
            direction = "▲" if stock.change_pct > 0 else "▼"
            movers.append(f"{stock.ticker} {direction}{abs(stock.change_pct):.1f}%")

    news_text = "\n".join(news_lines) if news_lines else "ニュースなし"
    movers_text = "\n".join(movers) if movers else "なし"

    return f"""以下は本日の株式市場のニュースと値動きです。

## 直近ニュース
{news_text}

## 主な値動き（±1%以上）
{movers_text}

上記をもとに、投資家向けに今日の注目ポイントを①②③の3点で簡潔に教えてください。
各ポイントは1〜2文で具体的に。"""


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
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return SummaryResult(key_points=lines)
    except Exception as e:
        logger.error("Claude API error: %s", e)
        return None
