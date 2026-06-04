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


def _build_prompt(
    news_items: list[NewsItem],
    market_data: dict,
    mover_news: dict[str, list[NewsItem]] | None = None,
) -> str:
    movers: list[PriceData] = []
    for stock in market_data.get("us_stocks", []) + market_data.get("jp_stocks", []):
        if isinstance(stock, PriceData) and abs(stock.change_pct) >= 1.0:
            movers.append(stock)
    movers.sort(key=lambda s: abs(s.change_pct), reverse=True)

    mover_detail_sections: list[str] = []
    for s in movers[:10]:
        direction = "▲" if s.change_pct > 0 else "▼"
        header = f"### {s.ticker} ({s.name}) {direction}{abs(s.change_pct):.1f}%"

        lines: list[str] = []
        if mover_news:
            for item in mover_news.get(s.ticker, [])[:5]:
                lines.append(f"  - [{item.source}] {item.title}")
        for item in news_items:
            if s.ticker in item.tickers and len(lines) < 8:
                lines.append(f"  - [{item.source}] {item.title}")

        section = header + ("\n" + "\n".join(lines) if lines else "\n  (関連ニュースなし)")
        mover_detail_sections.append(section)

    general_lines: list[str] = []
    for item in news_items[:30]:
        if not item.tickers:
            general_lines.append(f"  [{item.source}] {item.title}")

    mover_tickers = [s.ticker for s in movers]
    ticker_list = "\n".join(f"- {t}" for t in mover_tickers) if mover_tickers else "（なし）"

    mover_details = "\n\n".join(mover_detail_sections) if mover_detail_sections else "（値動きなし）"
    general_text = "\n".join(general_lines) if general_lines else "（なし）"

    return f"""以下は本日の株式市場データです。各銘柄の値動きの背景をニュースから読み解いてください。

## 値動き銘柄別ニュース詳細
（各銘柄のニュースを確認し、値動きの理由を特定してください）

{mover_details}

## 市場全般ニュース（補足）
{general_text}

---

上記をもとに、以下の形式で回答してください。

【値動きの背景】
以下の各銘柄について、上記ニュースに基づいて値動きの具体的な理由を1〜2文で説明してください。
（「〇〇が発表した…により…」のように、具体的なニュース内容に言及してください）
{ticker_list}

（銘柄コード）: （ニュースに基づく具体的な値動き理由。該当ニュースがなければ「関連ニュースなし」）

【今日の注目ポイント】
① （市場全体への影響・投資家が注目すべきポイントを1〜2文で）
② （セクター・テーマへの波及効果や注意点を1〜2文で）
③ （今後の見通しや注目イベントを1〜2文で）"""


def _parse_response(text: str, market_data: dict) -> SummaryResult:
    mover_tickers: set[str] = set()
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
    mover_news: dict[str, list[NewsItem]] | None = None,
) -> SummaryResult | None:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = _build_prompt(news_items, market_data, mover_news)
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
