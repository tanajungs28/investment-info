# Phase 3 セットアップ手順（Firebase + Vercel）

コードは Firebase のキーがなくても動く設計です:
- **エージェント**: `FIREBASE_PROJECT_ID` 未設定なら永続化をスキップして Slack 投稿のみ行う
- **ダッシュボード**: Firebase 未接続ならデモデータを表示（DEMO DATA バッジ付き）

Vercel デプロイと GitHub 連携は設定済み:
- 本番 URL: https://investment-dashboard-rosy-six.vercel.app
- main への push で自動デプロイ（Root Directory = `dashboard`）

以下を済ませると本稼働に切り替わります。

---

## 1. Firebase プロジェクト作成

1. https://console.firebase.google.com → プロジェクトを追加（無料の Spark プランでOK）
2. 構築 → **Firestore Database** → データベースを作成
   - ロケーション: `asia-northeast1`（東京）推奨
   - **本番環境モード**で開始
3. Firestore の「ルール」タブに `storage/firestore.rules` の内容を貼り付けて公開
   （`daily_reports` コレクションのみ誰でも読み取り可・書き込みは不可）

## 2. キーの取得（2種類）

### サービスアカウント（エージェントの書き込み用・秘匿）

プロジェクトの設定（歯車）→ サービスアカウント → **新しい秘密鍵の生成**
→ JSON ファイルがダウンロードされる。**中身の JSON 文字列全体**を使う。

### Web API キー（ダッシュボードの読み取り用・公開可）

プロジェクトの設定 → 全般 → 「ウェブ API キー」をコピー。
（表示されない場合はアプリの追加 → ウェブを一度作成すると表示される）

あわせて**プロジェクト ID**（設定 → 全般）も控える。

## 3. エージェント側の設定

### GitHub Actions（本番）

リポジトリの Settings → Secrets and variables → Actions に追加:

| Secret 名 | 値 |
|---|---|
| `FIREBASE_PROJECT_ID` | プロジェクト ID |
| `FIREBASE_SERVICE_ACCOUNT` | サービスアカウント JSON の中身（1ファイル丸ごと） |

### ローカル（手動実行用・任意）

`.env` に追記（JSON は1行に潰して貼る）:

```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"...",...}
```

## 4. ダッシュボード側の設定（Vercel）

```bash
cd dashboard
vercel env add NEXT_PUBLIC_FIREBASE_PROJECT_ID production
vercel env add NEXT_PUBLIC_FIREBASE_API_KEY production
vercel deploy --prod --yes
```

（または Vercel ダッシュボードの Project Settings → Environment Variables から）

## 5. 動作確認

- エージェント実行後、Firebase Console の Firestore で
  `daily_reports/{日付}` ドキュメントが入っていること
- ダッシュボード URL で DEMO DATA バッジが**消えている**こと
- スパークラインは履歴が2日分以上溜まると表示される

## データモデル

`daily_reports/{YYYY-MM-DD}` に1日1ドキュメント:

```
snapshot_date: "2026-06-12"
market:   [ {category, ticker, name, price, change_pct, volume, avg_volume} ]
news:     [ {title, url, source, published, tickers} ]
calendar: [ {time, currency, title, importance} ]
summary:  { key_points: [...], mover_explanations: {ticker: 説明} } | null
```

書き込みは1日1回の upsert のみなので Spark プランの無料枠で十分収まる。

## ローカル開発

```bash
cd dashboard
pnpm install
pnpm dev   # http://localhost:3000 （キー未設定ならデモデータ）
```
