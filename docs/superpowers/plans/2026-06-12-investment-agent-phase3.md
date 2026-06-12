# 投資情報収集AIエージェント Phase 3 実装計画

**Goal:** Firestore でのデータ蓄積・履歴管理 + Next.js Web ダッシュボード + Vercel デプロイ。

**Status:** コード実装完了 (2026-06-12)。Vercel デプロイ・GitHub 連携済み。
Firebase プロジェクト作成のみ未了（手順: `docs/phase3-setup.md`）。

> 当初 Supabase で実装したが、無料枠を使い切っていたため
> 同日中に Firebase (Firestore) へ移行した。

---

## Task 1: Firestore 永続化（Python 側）

- [x] `storage/firestore_store.py` — Firestore REST API へ requests で upsert。
      firebase-admin は使わず google-auth のみ追加（軽量・テスト容易）。
      `daily_reports/{日付}` に1日1ドキュメント（market/news/calendar/summary をネスト）
- [x] `storage/firestore.rules` — daily_reports は public read、書き込みは
      サービスアカウント（ルールバイパス）のみ
- [x] `main.py` — `FIREBASE_PROJECT_ID` / `FIREBASE_SERVICE_ACCOUNT`（JSON文字列）
      があれば保存、なければスキップ。永続化失敗でも Slack 投稿は継続
- [x] Actions ワークフローに secrets を追加（未設定なら空で無害）
- [x] テスト 9 件（storage 7 / main 2）

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

## 完了済みのデプロイ設定

- [x] Vercel プロジェクト作成・本番デプロイ（https://investment-dashboard-rosy-six.vercel.app）
- [x] Root Directory = `dashboard` 設定、GitHub 連携（main push で自動デプロイ）

## 残作業（ユーザー側）

- [ ] Firebase プロジェクト作成 + Firestore 有効化 + `storage/firestore.rules` 適用
- [ ] GitHub Actions secrets（FIREBASE_PROJECT_ID / FIREBASE_SERVICE_ACCOUNT）
- [ ] Vercel 環境変数（NEXT_PUBLIC_FIREBASE_PROJECT_ID / NEXT_PUBLIC_FIREBASE_API_KEY）
- [ ] `.env.example` への Firebase 変数追記（権限制約でツールから編集不可だった）

## 将来のアラート（要件 5-2、未着手）

- 急騰急落 ±5% の随時アラート、決算直前通知（`#alerts` チャンネル）
