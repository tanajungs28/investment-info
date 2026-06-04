# 投資情報収集AIエージェント Phase 1 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 毎朝6:00 JSTに日米株式市場データを自動収集し、Claude APIで要約してSlack `#morning-report` へ投稿するPythonエージェントのPhase 1を完成させる。

**Architecture:** モジュール分割構成。`collectors/` がデータ取得（yfinance・RSS・カレンダー）、`reporters/` がClaude要約とSlack投稿、`main.py` がオーケストレーションを担当。各モジュールは独立してテスト可能。

**Tech Stack:** Python 3.11+, yfinance, feedparser, anthropic SDK, requests, PyYAML, python-dotenv, pytest, responses

---

## ファイルマップ

| ファイル | 役割 |
|---------|------|
| `config/watchlist.yaml` | 監視銘柄・指数・ETF・セクター定義 |
| `config/settings.yaml` | RSS URL・Slack設定・Claude設定 |
| `collectors/market.py` | yfinanceで株価・指数・為替・セクターETF取得 |
| `collectors/news.py` | RSSパース・銘柄マッチング |
| `collectors/calendar.py` | Forex Factory RSSで経済指標カレンダー取得 |
| `reporters/claude_client.py` | Claude APIでニュース要約・注目ポイント生成 |
| `reporters/slack.py` | Block Kit形式でSlack Webhookへ投稿 |
| `main.py` | 全コンポーネントを統合・実行エントリーポイント |
| `tests/test_market.py` | market.py のユニットテスト |
| `tests/test_news.py` | news.py のユニットテスト |
| `tests/test_calendar.py` | calendar.py のユニットテスト |
| `tests/test_claude_client.py` | claude_client.py のユニットテスト |
| `tests/test_slack.py` | slack.py のユニットテスト |
| `tests/test_main.py` | main.py の統合テスト |
| `com.investment-agent.morning-report.plist` | macOS launchd で6時定時実行 |

---

## Task 1: プロジェクトスキャフォールディング

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `collectors/__init__.py`
- Create: `reporters/__init__.py`
- Create: `tests/__init__.py`
- Create: `logs/.gitkeep`

- [ ] **Step 1: ディレクトリ構造を作成**

```bash
mkdir -p collectors reporters tests logs config
touch collectors/__init__.py reporters/__init__.py tests/__init__.py
touch logs/.gitkeep
```

- [ ] **Step 2: requirements.txt を作成**

```
yfinance>=0.2.40
anthropic>=0.34.0
feedparser>=6.0.11
requests>=2.32.0
python-dotenv>=1.0.0
pyyaml>=6.0.1
beautifulsoup4>=4.12.0
lxml>=5.0.0
pandas>=2.2.0
pytest>=8.0.0
pytest-mock>=3.14.0
responses>=0.25.0
```

- [ ] **Step 3: .env.example を作成**

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/TXXXXXXXX/BXXXXXXXX/xxxxxxxx
```

- [ ] **Step 4: .gitignore を作成**

```
.env
__pycache__/
*.pyc
*.pyo
.pytest_cache/
logs/error.log
logs/stdout.log
logs/stderr.log
venv/
```

- [ ] **Step 5: 仮想環境を作成して依存をインストール**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 6: Commit**

```bash
git init
git add .
git commit -m "chore: initial project scaffolding"
```

---

## Task 2: 設定ファイル

**Files:**
- Create: `config/watchlist.yaml`
- Create: `config/settings.yaml`

- [ ] **Step 1: config/watchlist.yaml を作成**

```yaml
indices:
  us:
    - ticker: "^GSPC"
      name: "S&P 500"
    - ticker: "^IXIC"
      name: "NASDAQ"
    - ticker: "^DJI"
      name: "Dow Jones"
  jp:
    - ticker: "^N225"
      name: "日経225"
    - ticker: "^TOPIX"
      name: "TOPIX"

forex:
  - ticker: "JPY=X"
    name: "USD/JPY"
  - ticker: "EURUSD=X"
    name: "EUR/USD"

stocks:
  us:
    - ticker: "AAPL"
      name: "Apple"
      style: "growth"
    - ticker: "MSFT"
      name: "Microsoft"
      style: "growth"
    - ticker: "NVDA"
      name: "NVIDIA"
      style: "growth"
    - ticker: "MU"
      name: "Micron Technology"
      style: "growth"
    - ticker: "WDC"
      name: "Western Digital"
      style: "growth"
    - ticker: "JNJ"
      name: "Johnson & Johnson"
      style: "dividend"
    - ticker: "PG"
      name: "Procter & Gamble"
      style: "dividend"
    - ticker: "MO"
      name: "Altria Group"
      style: "dividend"
    - ticker: "PFE"
      name: "Pfizer"
      style: "dividend"
    - ticker: "SFL"
      name: "SFL Corporation"
      style: "dividend"
    - ticker: "VZ"
      name: "Verizon"
      style: "dividend"
    - ticker: "WU"
      name: "Western Union"
      style: "dividend"
  jp:
    - ticker: "7203.T"
      name: "トヨタ自動車"
      style: "swing"
    - ticker: "6758.T"
      name: "ソニーグループ"
      style: "swing"
    - ticker: "6861.T"
      name: "キーエンス"
      style: "swing"
    - ticker: "9984.T"
      name: "ソフトバンクグループ"
      style: "swing"
    - ticker: "8035.T"
      name: "東京エレクトロン"
      style: "swing"

sectors:
  us:
    - ticker: "XLK"
      name: "テクノロジー"
    - ticker: "XLC"
      name: "コミュニケーション・サービス"
    - ticker: "XLY"
      name: "一般消費財"
    - ticker: "XLP"
      name: "生活必需品"
    - ticker: "XLV"
      name: "ヘルスケア"
    - ticker: "XLF"
      name: "金融"
    - ticker: "XLI"
      name: "資本財・サービス"
    - ticker: "XLB"
      name: "素材"
    - ticker: "XLRE"
      name: "不動産"
    - ticker: "XLU"
      name: "公益事業"
    - ticker: "XLE"
      name: "エネルギー"
  jp:
    - ticker: "1615.T"
      name: "銀行業"
    - ticker: "1617.T"
      name: "食料品"
    - ticker: "1618.T"
      name: "石油・石炭製品"
    - ticker: "1619.T"
      name: "建設業"
    - ticker: "1620.T"
      name: "化学"
    - ticker: "1621.T"
      name: "医薬品"
    - ticker: "1622.T"
      name: "輸送用機器"
    - ticker: "1623.T"
      name: "鉄鋼・非鉄金属"
    - ticker: "1624.T"
      name: "機械"
    - ticker: "1625.T"
      name: "電気機器"
    - ticker: "1626.T"
      name: "情報・通信業"
    - ticker: "1627.T"
      name: "その他金融業"
    - ticker: "1628.T"
      name: "不動産業"
```

- [ ] **Step 2: config/settings.yaml を作成**

```yaml
slack:
  channel: "#morning-report"
  report_time: "06:00"
  timezone: "Asia/Tokyo"

news:
  lookback_hours: 24
  rss_feeds:
    jp:
      - url: "https://kabutan.jp/news/rss/"
        name: "株探"
      - url: "https://feeds.reuters.com/reuters/JPBusinessNews"
        name: "Reuters Japan"

calendar:
  forex_factory_rss: "https://www.forexfactory.com/ff_calendar_thisweek.xml"
  min_importance: 2

claude:
  model: "claude-haiku-4-5-20251001"
  max_tokens: 1000
```

- [ ] **Step 3: Commit**

```bash
git add config/
git commit -m "chore: add watchlist and settings config"
```

---

## Task 3: Market Collector

**Files:**
- Create: `collectors/market.py`
- Create: `tests/test_market.py`

- [ ] **Step 1: テストを書く (RED)**

`tests/test_market.py` を作成:

```python
from unittest.mock import MagicMock, patch
from collectors.market import get_price_data, get_market_data, PriceData


def make_mock_ticker(price=100.0, prev_close=98.0, volume=1000000, avg_volume=900000):
    ticker = MagicMock()
    ticker.fast_info.last_price = price
    ticker.fast_info.previous_close = prev_close
    ticker.fast_info.three_month_average_volume = avg_volume
    ticker.info = {"regularMarketVolume": volume}
    return ticker


@patch("collectors.market.yf.Ticker")
def test_get_price_data_returns_price_data(mock_ticker_cls):
    mock_ticker_cls.return_value = make_mock_ticker(price=150.0, prev_close=145.0)
    result = get_price_data("AAPL", "Apple")
    assert isinstance(result, PriceData)
    assert result.ticker == "AAPL"
    assert result.name == "Apple"
    assert result.price == 150.0
    assert abs(result.change_pct - 3.45) < 0.1


@patch("collectors.market.yf.Ticker")
def test_get_price_data_returns_none_on_missing_price(mock_ticker_cls):
    mock_ticker_cls.return_value.fast_info.last_price = None
    result = get_price_data("INVALID", "Invalid")
    assert result is None


@patch("collectors.market.get_price_data")
def test_get_market_data_returns_all_sections(mock_get_price):
    mock_get_price.return_value = PriceData(
        ticker="TEST", name="Test", price=100.0, change_pct=1.0
    )
    data = get_market_data(
        indices=[{"ticker": "^GSPC", "name": "S&P 500"}],
        forex=[],
        us_stocks=[],
        jp_stocks=[],
        us_sectors=[],
        jp_sectors=[],
    )
    assert "indices" in data
    assert "us_stocks" in data
    assert "timestamp" in data
    assert len(data["indices"]) == 1
    assert data["indices"][0].ticker == "TEST"
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_market.py -v
```

Expected: `FAILED` with `ModuleNotFoundError: No module named 'collectors.market'`

- [ ] **Step 3: collectors/market.py を実装**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import logging
import time

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    ticker: str
    name: str
    price: float
    change_pct: float
    volume: int | None = None
    avg_volume: int | None = None


def get_price_data(ticker: str, name: str, retries: int = 3) -> PriceData | None:
    for attempt in range(retries):
        try:
            t = yf.Ticker(ticker)
            price = t.fast_info.last_price
            prev_close = t.fast_info.previous_close
            if price is None or prev_close is None:
                return None
            change_pct = (price - prev_close) / prev_close * 100
            volume = t.info.get("regularMarketVolume")
            avg_volume = t.fast_info.three_month_average_volume
            return PriceData(
                ticker=ticker,
                name=name,
                price=round(price, 2),
                change_pct=round(change_pct, 2),
                volume=volume,
                avg_volume=int(avg_volume) if avg_volume else None,
            )
        except Exception as e:
            logger.warning("Attempt %d failed for %s: %s", attempt + 1, ticker, e)
            if attempt < retries - 1:
                time.sleep(1)
    return None


def get_market_data(
    indices: list[dict],
    forex: list[dict],
    us_stocks: list[dict],
    jp_stocks: list[dict],
    us_sectors: list[dict],
    jp_sectors: list[dict],
) -> dict:
    def fetch_list(items: list[dict]) -> list[PriceData]:
        results = []
        for item in items:
            data = get_price_data(item["ticker"], item["name"])
            if data:
                results.append(data)
        return results

    return {
        "indices": fetch_list(indices),
        "forex": fetch_list(forex),
        "us_stocks": fetch_list(us_stocks),
        "jp_stocks": fetch_list(jp_stocks),
        "us_sectors": fetch_list(us_sectors),
        "jp_sectors": fetch_list(jp_sectors),
        "timestamp": datetime.now(),
    }
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_market.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add collectors/market.py tests/test_market.py
git commit -m "feat: add market data collector with yfinance"
```

---

## Task 4: News Collector

**Files:**
- Create: `collectors/news.py`
- Create: `tests/test_news.py`

- [ ] **Step 1: テストを書く (RED)**

`tests/test_news.py` を作成:

```python
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from collectors.news import fetch_rss_news, match_tickers, collect_news, NewsItem


def make_entry(title: str, published: datetime) -> MagicMock:
    entry = MagicMock()
    entry.title = title
    entry.link = "https://example.com/news"
    entry.published_parsed = published.timetuple()
    return entry


@patch("collectors.news.feedparser.parse")
def test_fetch_rss_keeps_only_last_24h(mock_parse):
    now = datetime.now(timezone.utc)
    recent = make_entry("Recent news", now - timedelta(hours=12))
    old = make_entry("Old news", now - timedelta(hours=36))
    mock_parse.return_value.entries = [recent, old]
    items = fetch_rss_news("http://example.com/rss", "Test Source", lookback_hours=24)
    assert len(items) == 1
    assert items[0].title == "Recent news"


def test_match_tickers_finds_company_name():
    watchlist = [{"ticker": "NVDA", "name": "NVIDIA"}]
    item = NewsItem(
        title="NVIDIAが新型GPUを発表",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert "NVDA" in result[0].tickers


def test_match_tickers_finds_ticker_symbol():
    watchlist = [{"ticker": "AAPL", "name": "Apple"}]
    item = NewsItem(
        title="AAPL hits record high",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert "AAPL" in result[0].tickers


def test_match_tickers_strips_dot_t_for_jp_stocks():
    watchlist = [{"ticker": "7203.T", "name": "トヨタ自動車"}]
    item = NewsItem(
        title="トヨタ自動車が増産を発表",
        url="http://example.com",
        source="Test",
        published=datetime.now(timezone.utc),
        tickers=[],
    )
    result = match_tickers([item], watchlist)
    assert "7203.T" in result[0].tickers
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_news.py -v
```

Expected: `FAILED` with `ModuleNotFoundError: No module named 'collectors.news'`

- [ ] **Step 3: collectors/news.py を実装**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import calendar
import logging

import feedparser

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published: datetime
    tickers: list[str] = field(default_factory=list)


def fetch_rss_news(
    url: str, source_name: str, lookback_hours: int = 24
) -> list[NewsItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries:
            try:
                published = datetime.fromtimestamp(
                    calendar.timegm(entry.published_parsed), tz=timezone.utc
                )
            except Exception:
                continue
            if published < cutoff:
                continue
            items.append(
                NewsItem(
                    title=entry.title,
                    url=entry.link,
                    source=source_name,
                    published=published,
                )
            )
        return items
    except Exception as e:
        logger.warning("Failed to fetch RSS from %s: %s", url, e)
        return []


def match_tickers(items: list[NewsItem], watchlist: list[dict]) -> list[NewsItem]:
    for item in items:
        for stock in watchlist:
            ticker_bare = stock["ticker"].replace(".T", "")
            name = stock["name"]
            title_upper = item.title.upper()
            if ticker_bare.upper() in title_upper or name in item.title:
                if stock["ticker"] not in item.tickers:
                    item.tickers.append(stock["ticker"])
    return items


def collect_news(
    rss_feeds: list[dict],
    all_stocks: list[dict],
    lookback_hours: int = 24,
) -> list[NewsItem]:
    items: list[NewsItem] = []
    for feed in rss_feeds:
        fetched = fetch_rss_news(feed["url"], feed["name"], lookback_hours)
        items.extend(fetched)
    items = match_tickers(items, all_stocks)
    items.sort(key=lambda x: x.published, reverse=True)
    return items
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_news.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add collectors/news.py tests/test_news.py
git commit -m "feat: add RSS news collector with ticker matching"
```

---

## Task 5: Economic Calendar Collector

**Files:**
- Create: `collectors/calendar.py`
- Create: `tests/test_calendar.py`

- [ ] **Step 1: テストを書く (RED)**

`tests/test_calendar.py` を作成:

```python
from unittest.mock import patch, MagicMock
from collectors.calendar import parse_forex_factory_events, EconomicEvent
import time


def make_entry(title: str, description: str, importance_label: str) -> MagicMock:
    entry = MagicMock()
    entry.title = title
    entry.get = lambda key, default="": description if key == "description" else default
    entry.published_parsed = time.strptime("Wed, 04 Jun 2025 13:30:00 +0000", "%a, %d %b %Y %H:%M:%S %z")
    return entry


@patch("collectors.calendar.feedparser.parse")
def test_parse_returns_high_importance_events(mock_parse):
    mock_parse.return_value.entries = [
        make_entry("CPI (MoM)", "High|USD|CPI|0.3%|0.2%", "High"),
        make_entry("Minor Data", "Low|USD|Minor||", "Low"),
    ]
    events = parse_forex_factory_events("http://example.com/rss", min_importance=2)
    assert len(events) == 1
    assert events[0].title == "CPI (MoM)"
    assert events[0].importance == 3


@patch("collectors.calendar.feedparser.parse")
def test_parse_returns_empty_list_on_error(mock_parse):
    mock_parse.side_effect = Exception("Network error")
    events = parse_forex_factory_events("http://example.com/rss")
    assert events == []


def test_economic_event_dataclass():
    event = EconomicEvent(time="22:30", currency="USD", title="FOMC", importance=3)
    assert event.currency == "USD"
    assert event.importance == 3
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_calendar.py -v
```

Expected: `FAILED` with `ModuleNotFoundError: No module named 'collectors.calendar'`

- [ ] **Step 3: collectors/calendar.py を実装**

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

import feedparser

logger = logging.getLogger(__name__)

IMPORTANCE_MAP = {"High": 3, "Medium": 2, "Low": 1}


@dataclass
class EconomicEvent:
    time: str
    currency: str
    title: str
    importance: int


def parse_forex_factory_events(
    url: str, min_importance: int = 2
) -> list[EconomicEvent]:
    try:
        feed = feedparser.parse(url)
        events = []
        for entry in feed.entries:
            description = entry.get("description", "")
            parts = description.split("|")
            if len(parts) < 2:
                continue
            importance_str = parts[0].strip()
            currency = parts[1].strip()
            importance = IMPORTANCE_MAP.get(importance_str, 0)
            if importance < min_importance:
                continue
            try:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                time_str = published.strftime("%H:%M")
            except Exception:
                time_str = "??:??"
            events.append(
                EconomicEvent(
                    time=time_str,
                    currency=currency,
                    title=entry.title,
                    importance=importance,
                )
            )
        return events
    except Exception as e:
        logger.warning("Failed to fetch economic calendar: %s", e)
        return []
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_calendar.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add collectors/calendar.py tests/test_calendar.py
git commit -m "feat: add economic calendar collector from Forex Factory RSS"
```

---

## Task 6: Claude API Client

**Files:**
- Create: `reporters/claude_client.py`
- Create: `tests/test_claude_client.py`

- [ ] **Step 1: テストを書く (RED)**

`tests/test_claude_client.py` を作成:

```python
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from reporters.claude_client import generate_summary, SummaryResult
from collectors.news import NewsItem
from collectors.market import PriceData


def make_news_items() -> list[NewsItem]:
    return [
        NewsItem(
            title="NVIDIAが新型GPU発表",
            url="http://example.com",
            source="株探",
            published=datetime.now(timezone.utc),
            tickers=["NVDA"],
        )
    ]


def make_market_data() -> dict:
    return {
        "us_stocks": [PriceData("NVDA", "NVIDIA", 900.0, 3.5)],
        "jp_stocks": [],
    }


@patch("reporters.claude_client.anthropic.Anthropic")
def test_generate_summary_returns_summary_result(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="① ポイント1\n② ポイント2\n③ ポイント3")]
    mock_client.messages.create.return_value = mock_response

    result = generate_summary(make_news_items(), make_market_data(), api_key="test-key")
    assert isinstance(result, SummaryResult)
    assert len(result.key_points) >= 1


@patch("reporters.claude_client.anthropic.Anthropic")
def test_generate_summary_returns_none_on_api_error(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.side_effect = Exception("API error")

    result = generate_summary([], {}, api_key="test-key")
    assert result is None
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_claude_client.py -v
```

Expected: `FAILED` with `ModuleNotFoundError: No module named 'reporters.claude_client'`

- [ ] **Step 3: reporters/claude_client.py を実装**

```python
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
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_claude_client.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add reporters/claude_client.py tests/test_claude_client.py
git commit -m "feat: add Claude API client for news summarization"
```

---

## Task 7: Slack Reporter

**Files:**
- Create: `reporters/slack.py`
- Create: `tests/test_slack.py`

- [ ] **Step 1: テストを書く (RED)**

`tests/test_slack.py` を作成:

```python
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
        "summary": SummaryResult(key_points=["① CPIに注目", "② NVDAモメンタム", "③ 円安一服"]),
    }


def test_build_report_blocks_returns_non_empty_list():
    blocks = build_report_blocks(make_report_data())
    assert isinstance(blocks, list)
    assert len(blocks) > 0


def test_build_report_blocks_contains_sp500():
    blocks = build_report_blocks(make_report_data())
    all_text = " ".join(
        str(b.get("text", {}).get("text", "")) for b in blocks
    )
    assert "S&P 500" in all_text


def test_build_report_blocks_contains_claude_summary():
    blocks = build_report_blocks(make_report_data())
    all_text = " ".join(
        str(b.get("text", {}).get("text", "")) for b in blocks
    )
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
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_slack.py -v
```

Expected: `FAILED` with `ModuleNotFoundError: No module named 'reporters.slack'`

- [ ] **Step 3: reporters/slack.py を実装**

```python
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
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_slack.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add reporters/slack.py tests/test_slack.py
git commit -m "feat: add Slack reporter with Block Kit formatting"
```

---

## Task 8: メインオーケストレーター

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: テストを書く (RED)**

`tests/test_main.py` を作成:

```python
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from main import load_config, run


def test_load_config_has_required_keys():
    config = load_config()
    assert "indices" in config["watchlist"]
    assert "stocks" in config["watchlist"]
    assert "sectors" in config["watchlist"]
    assert "slack" in config["settings"]
    assert "news" in config["settings"]


@patch("main.post_report", return_value=True)
@patch("main.generate_summary", return_value=None)
@patch("main.parse_forex_factory_events", return_value=[])
@patch("main.collect_news", return_value=[])
@patch("main.get_market_data")
def test_run_calls_all_collectors_and_returns_true(
    mock_market, mock_news, mock_calendar, mock_summary, mock_post
):
    mock_market.return_value = {
        "indices": [], "forex": [], "us_stocks": [],
        "jp_stocks": [], "us_sectors": [], "jp_sectors": [],
        "timestamp": datetime.now(timezone.utc),
    }
    result = run(
        webhook_url="https://hooks.slack.com/test",
        anthropic_api_key="test-key",
    )
    assert result is True
    assert mock_market.called
    assert mock_news.called
    assert mock_calendar.called
    assert mock_post.called
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_main.py -v
```

Expected: `FAILED` with `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: main.py を実装**

```python
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
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_main.py -v
```

Expected: `2 passed`

- [ ] **Step 5: 全テストが通ることを確認**

```bash
pytest tests/ -v
```

Expected: All tests pass (14+ tests).

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main orchestrator integrating all collectors and reporters"
```

---

## Task 9: 手動実行テストと cron 設定

**Files:**
- Create: `.env`（gitignore済み・実キー記入）
- Create: `com.investment-agent.morning-report.plist`

- [ ] **Step 1: .env を実キーで作成**

```bash
cp .env.example .env
```

`.env` をエディタで開き、実際の値を設定:

```
ANTHROPIC_API_KEY=sk-ant-（実際のキー）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/（実際のURL）
```

- [ ] **Step 2: 手動実行で動作確認**

```bash
source venv/bin/activate
python main.py
```

Expected: ターミナルに `Report posted successfully.` が表示され、Slack `#morning-report` にレポートが投稿される。

- [ ] **Step 3: macOS launchd plist を作成**

`com.investment-agent.morning-report.plist` を作成（`YOUR_*` は実際の値に置き換えること）:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.investment-agent.morning-report</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/juntanaka/Applications/investment-info/venv/bin/python</string>
    <string>/Users/juntanaka/Applications/investment-info/main.py</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>6</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>EnvironmentVariables</key>
  <dict>
    <key>ANTHROPIC_API_KEY</key>
    <string>YOUR_ANTHROPIC_API_KEY</string>
    <key>SLACK_WEBHOOK_URL</key>
    <string>YOUR_SLACK_WEBHOOK_URL</string>
  </dict>
  <key>StandardOutPath</key>
  <string>/Users/juntanaka/Applications/investment-info/logs/stdout.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/juntanaka/Applications/investment-info/logs/stderr.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
```

- [ ] **Step 4: launchd に登録**

```bash
cp com.investment-agent.morning-report.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.investment-agent.morning-report.plist
launchctl list | grep investment-agent
```

Expected: `com.investment-agent.morning-report` が一覧に表示される。

- [ ] **Step 5: Commit**

```bash
git add com.investment-agent.morning-report.plist
git commit -m "chore: add launchd plist for 6:00 JST daily scheduling"
```
