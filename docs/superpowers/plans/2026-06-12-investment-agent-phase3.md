# 投資情報収集AIエージェント Phase 3 実装計画

**Goal:** Supabase でのデータ蓄積・履歴管理 + Next.js Web ダッシュボード + Vercel デプロイ。

**Status:** コード実装完了 (2026-06-12)。Supabase / Vercel のセットアップのみ未了
（手順: `docs/phase3-setup.md`）。

---

## Task 1: Supabase 永続化（Python 側）

- [x] `storage/supabase_store.py` — PostgREST API へ requests で直接 upsert
      （supabase-py 依存を増やさない）。`build_rows()` がレポートデータを
      4テーブル分の行に変換、`store_report()` がテーブル単位でエラー継続
- [x] `storage/schema.sql` — market_snapshots / news_items / calendar_events /
      daily_summaries。upsert 用 unique 制約 + RLS（anon は read のみ）
- [x] `main.py` — `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` があれば保存、
      なければスキップ。永続化失敗でも Slack 投稿は継続
- [x] Actions ワークフローに secrets を追加（未設定なら空で無害）
- [x] テスト 9 件追加（storage 7 / main 2）

## Task 2: Next.js ダッシュボード（`dashboard/`）

- [x] Next.js 15 + React 19 + TypeScript、App Router、サーバーコンポーネント
- [x] データ層 `lib/data.ts` — anon キーで PostgREST を直接 fetch
      （ISR revalidate 300秒）。キー未設定時は `lib/mock.ts` のデモデータ
- [x] ウォッチリスト一覧 — 価格・前日比・出来高比バッジ（2倍以上アンバー）・
      30日スパークライン（インラインSVG、外部チャートライブラリなし）・
      Claude の変動理由表示
- [x] セクターヒートマップ — 米国/日本、騰落率で色の濃淡（color-mix）
- [x] ニュースフィード — 銘柄フィルタチップ（URL クエリ `?ticker=` で状態保持）、
      タップでリンク先へ
- [x] 経済指標カレンダー + Claude 注目ポイントカード
- [x] デザイン: ダーク・マーケットターミナル。日本の市況慣習（上昇=朱赤/下落=緑）、
      tabular numerals、レイヤードサーフェス。First Load JS 107kB
- [x] 本番ビルド成功・デモモードでの全セクション描画とフィルタ動作を確認

## スコープ外 / 残作業（ユーザー側）

- [ ] Supabase プロジェクト作成 + `schema.sql` 実行
- [ ] GitHub Actions secrets（SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY）
- [ ] Vercel import（Root Directory = `dashboard`）+ 環境変数2つ
- [ ] `.env.example` への Supabase 変数追記（権限制約でツールから編集不可だった）

## 将来のアラート（要件 5-2、未着手）

- 急騰急落 ±5% の随時アラート、決算直前通知（`#alerts` チャンネル）
