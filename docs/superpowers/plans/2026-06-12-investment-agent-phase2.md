# 投資情報収集AIエージェント Phase 2 実装計画

**Goal:** 要件書「フェーズ2：精度向上」を実装する — 日本株ニュース収集の強化・セクター動向の可視化・出来高異常検知。

**Status:** 実装完了 (2026-06-12)

---

## 背景

Phase 1 で設定していた日本株ニュースフィードは2本とも取得不能になっていた
（株探 RSS = 404、Reuters Japan = DNS 解決不可）。そのため日本株ニュースは
実質的に yfinance の英語ニュースのみだった。

## Task 1: 日本株ニュース収集の強化

- [x] 死んだフィードを生きている3本に置換（`config/settings.yaml`）
  - Yahoo!ニュース 経済トピックス
  - NHK 経済ニュース
  - 日経 マーケットニュース（wor.jp ミラー / RDF形式）
- [x] RDF形式（dc:date → `updated_parsed`）の日付フォールバック対応（`collectors/news.py`）
- [x] 銘柄エイリアスマッチング: ウォッチリストに `aliases` を追加し、
      日本語メディアの表記（エヌビディア・トヨタ・東エレク 等）でもマッチ
- [x] 短いティッカー（MO, PG, MU 等）が単語の一部（MORNING 等）に
      誤マッチするバグを単語境界の正規表現で修正

## Task 2: 出来高異常検知

- [x] `PriceData.volume_ratio` プロパティ（出来高 ÷ 3ヶ月平均出来高）
- [x] `detect_volume_anomalies(stocks, threshold)` — 閾値以上を倍率降順で返す
- [x] 閾値は `settings.yaml` の `alerts.volume_spike_ratio`（既定 2.0倍）
- [x] Slack レポートに「⚡ 出来高急増アラート」セクションを追加
      （値動きが小さくても出来高が急増した銘柄を検知できる）

## Task 3: セクター動向の可視化

- [x] `_format_sector_bars()` — 全セクターを騰落率降順で並べ、
      Unicode バー（上昇 █ / 下落 ▒）で可視化。上位/下位3のみの表示から
      全セクターランキング表示に変更

## テスト

- 新規テスト 14 件追加（market 5 / news 4 / slack 4 / main 1）、計 45 件パス
- TDD（RED → GREEN）で実装。誤マッチバグは失敗テストで再現してから修正

## スコープ外（Phase 3 へ）

- Supabase でのデータ蓄積（設計書では Phase 2 だが、ダッシュボードと
  一体で Phase 3 にて実施。外部サービスのセットアップが必要）
- Web ダッシュボード（Next.js / Vercel）
