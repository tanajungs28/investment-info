# 投資情報収集AIエージェント 設計書

**作成日:** 2026-06-04  
**フェーズ:** Phase 1（ミニマム動作版）

---

## 1. 概要

毎朝6:00 JSTに日米株式市場の情報を自動収集し、Slackへ構造化レポートを投稿するPythonエージェント。

**ゴール:** Slack `#morning-report` チャンネルへの自動投稿が確認できる最小構成の動作版を作る。

---

## 2. アーキテクチャ

モジュール分割構成（Approach B）を採用。責務を明確に分離し、Phase 2（ダッシュボード）への拡張を容易にする。

```
investment-info/
├── config/
│   ├── watchlist.yaml        # 監視銘柄・指数・ETF定義
│   └── settings.yaml         # RSS URL・Slackチャンネル等
├── collectors/
│   ├── __init__.py
│   ├── market.py             # yfinance: 指数・個別株価・為替
│   ├── news.py               # RSS: 日本株ニュース + yfinance.news (米国株)
│   └── calendar.py           # 経済指標カレンダー (Forex Factory RSS)
├── reporters/
│   ├── __init__.py
│   ├── claude_client.py      # Claude API: 要約・注目ポイント生成
│   └── slack.py              # Slack Webhook投稿 (Block Kit)
├── logs/
│   └── error.log             # エラーログ出力先
├── main.py                   # オーケストレーター
├── requirements.txt
├── .env                      # シークレット (gitignore済み)
└── .env.example
```

---

## 3. データフロー

```
main.py 起動
  │
  ├─ collectors/market.py
  │     └─ yfinance → 指数 / 個別株 / 為替 / セクターETF
  │
  ├─ collectors/news.py
  │     └─ RSS取得 (株探, Reuters Japan)
  │          → 過去24時間に絞り込み
  │          → 銘柄名/ティッカーでマッチング
  │
  ├─ collectors/calendar.py
  │     └─ Forex Factory RSS → 当日・翌日の重要指標を抽出
  │
  ├─ reporters/claude_client.py
  │     └─ ニュース一覧 + 市場データ → Claude API
  │          → ニュース要約 + 今日の注目ポイント3行
  │
  └─ reporters/slack.py
        └─ 全データを組み立て → Slack Webhook POST
```

---

## 4. ウォッチリスト (watchlist.yaml)

### 指数

| ティッカー | 名称 |
|-----------|------|
| `^GSPC` | S&P 500 |
| `^IXIC` | NASDAQ |
| `^DJI` | Dow Jones |
| `^N225` | 日経225 |
| `^TOPIX` | TOPIX |

### 為替

| ティッカー | ペア |
|-----------|------|
| `JPY=X` | USD/JPY |
| `EURUSD=X` | EUR/USD |

### 米国株

| ティッカー | 名称 | スタイル |
|-----------|------|---------|
| AAPL | Apple | growth |
| MSFT | Microsoft | growth |
| NVDA | NVIDIA | growth |
| MU | Micron Technology | growth |
| WDC | Western Digital | growth |
| JNJ | Johnson & Johnson | dividend |
| PG | Procter & Gamble | dividend |
| MO | Altria Group | dividend |
| PFE | Pfizer | dividend |
| SFL | SFL Corporation | dividend |
| VZ | Verizon | dividend |
| WU | Western Union | dividend |

### 日本株

| ティッカー | 名称 | スタイル |
|-----------|------|---------|
| 7203.T | トヨタ自動車 | swing |
| 6758.T | ソニーグループ | swing |
| 6861.T | キーエンス | swing |
| 9984.T | ソフトバンクグループ | swing |
| 8035.T | 東京エレクトロン | swing |

### セクターETF（米国 GICS全11セクター）

SPDR Select Sector ETF シリーズで全セクターを網羅する。

| ティッカー | セクター（日本語） |
|-----------|-----------------|
| XLK | テクノロジー |
| XLC | コミュニケーション・サービス |
| XLY | 一般消費財 |
| XLP | 生活必需品 |
| XLV | ヘルスケア |
| XLF | 金融 |
| XLI | 資本財・サービス |
| XLB | 素材 |
| XLRE | 不動産 |
| XLU | 公益事業 |
| XLE | エネルギー |

### 東証33業種インデックス（日本 全セクター）

yfinanceで直接取得できない業種は、代表的なセクターETF（例：`1615.T` NEXT FUNDS 東証銀行業等）または個別銘柄の平均で代替する。

| コード | 業種名 |
|-------|-------|
| 1 | 水産・農林業 |
| 2 | 鉱業 |
| 3 | 建設業 |
| 4 | 食料品 |
| 5 | 繊維製品 |
| 6 | パルプ・紙 |
| 7 | 化学 |
| 8 | 医薬品 |
| 9 | 石油・石炭製品 |
| 10 | ゴム製品 |
| 11 | ガラス・土石製品 |
| 12 | 鉄鋼 |
| 13 | 非鉄金属 |
| 14 | 金属製品 |
| 15 | 機械 |
| 16 | 電気機器 |
| 17 | 輸送用機器 |
| 18 | 精密機器 |
| 19 | その他製品 |
| 20 | 電気・ガス業 |
| 21 | 陸運業 |
| 22 | 海運業 |
| 23 | 空運業 |
| 24 | 倉庫・運輸関連業 |
| 25 | 情報・通信業 |
| 26 | 卸売業 |
| 27 | 小売業 |
| 28 | 銀行業 |
| 29 | 証券・商品先物取引業 |
| 30 | 保険業 |
| 31 | その他金融業 |
| 32 | 不動産業 |
| 33 | サービス業 |

**データ取得方針:** 東証33業種の騰落率は、JPX（日本取引所グループ）が公開するCSVデータ（`https://www.jpx.co.jp/markets/statistics-equities/sector/`）をHTTPで取得してパースする。yfinanceでは業種インデックスが取得できないため、JPXの公式データを一次ソースとする。

---

## 5. 外部データソース

| カテゴリ | ソース | 取得方法 |
|---------|--------|---------|
| 株価・指数・ETF | Yahoo Finance | yfinance |
| 為替 | Yahoo Finance | yfinance |
| 米国株ニュース | Yahoo Finance | yfinance `.news` |
| 日本株ニュース | 株探 RSS / Reuters Japan RSS | feedparser |
| 経済指標カレンダー | Forex Factory RSS | feedparser + XML解析 |

---

## 6. Slackレポートフォーマット

Block Kit形式で以下のセクションを順番に投稿する。

```
📊 市場サマリー               YYYY-MM-DD (曜) 06:00 JST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
S&P 500   5,234.18  +0.82% ▲
NASDAQ    16,340.87  -0.21% ▼
Dow Jones 38,871.00  +0.45% ▲
日経225   38,460.25  +1.12% ▲
TOPIX      2,734.11  +0.88% ▲
USD/JPY      157.23
EUR/USD        1.083

🗓 本日の経済指標
  15:30 USD  消費者物価指数(CPI)  ★★★
  23:00 USD  FOMC議事録公表       ★★★

📈 セクター動向（米国）
  上位: テクノロジー +1.4% / ヘルスケア +0.9% / 金融 +0.6%
  下位: エネルギー -0.8% / 素材 -0.5%

🔍 ウォッチ銘柄ハイライト
  NVDA  892.10  +3.21% ▲  出来高: 通常比 2.1倍
  MU    128.45  -2.10% ▼
  7203.T 3,250   +1.50% ▲

📰 注目ニュース
  [NVDA] エヌビディア、次世代GPU「Blackwell Ultra」量産開始へ
  [MU]   マイクロン、中国向け輸出規制強化の影響を警告
  [7203.T] トヨタ、北米販売台数が過去最高を更新

💡 今日の注目ポイント（Claude）
  ① CPIの結果次第でFRBの利下げ観測が大きく動く可能性。
  ② NVDAは出来高急増を伴う上昇で、モメンタム継続に注目。
  ③ 円安一服の兆しあり、輸出株（トヨタ等）の上値が重くなるか。
```

---

## 7. エラーハンドリング

| 障害パターン | 対応 |
|-------------|------|
| yfinanceタイムアウト | 3回リトライ後、該当セクションを「取得失敗」と表示して続行 |
| RSSフィード取得失敗 | ニュースセクションを省略してレポート投稿は継続 |
| Claude API エラー | 要約セクションをスキップ、「要約生成に失敗しました」と記載 |
| Slack投稿失敗 | エラーログを `logs/error.log` に出力 |

**基本方針:** 一部のデータ取得に失敗しても、取得できた情報でレポートを投稿する。完全失敗のみログに記録。

---

## 8. 実行環境

- **Phase 1:** ローカルMacで `python main.py` を手動実行 or macOS `launchd` で定時実行
- **将来:** GitHub Actions またはクラウド（Fly.io 等）へ移行可能な設計にする
- **スケジューラ:** Phase 1はシステムcron/launchd。APSchedulerはPhase 2以降で検討

---

## 9. 環境変数 (.env)

```
ANTHROPIC_API_KEY=sk-ant-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## 10. 開発フェーズ

| フェーズ | 内容 |
|---------|------|
| Phase 1（本設計書のスコープ） | yfinance + RSS + Claude API + Slack投稿 + cron |
| Phase 2 | 日本株ニュース強化・出来高異常検知・Supabaseでデータ蓄積 |
| Phase 3 | Next.js Webダッシュボード・Vercelデプロイ |
