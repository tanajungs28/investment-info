# Phase 3 セットアップ手順（Supabase + Vercel）

コードは Supabase / Vercel のキーがなくても動く設計です:
- **エージェント**: `SUPABASE_URL` 未設定なら永続化をスキップして Slack 投稿のみ行う
- **ダッシュボード**: Supabase 未接続ならデモデータを表示（DEMO DATA バッジ付き）

以下を済ませると本稼働に切り替わります。

---

## 1. Supabase プロジェクト作成

1. https://supabase.com → New project（無料枠でOK、リージョンは Tokyo 推奨）
2. SQL Editor で `storage/schema.sql` の内容を実行（テーブル4つ + RLS 設定）
3. Project Settings → API から以下を控える:
   - **Project URL** (`https://xxxx.supabase.co`)
   - **service_role key**（エージェントの書き込み用・秘匿）
   - **anon key**（ダッシュボードの読み取り用・公開可）

## 2. エージェント側の設定

### GitHub Actions（本番）

リポジトリの Settings → Secrets and variables → Actions に追加:

| Secret 名 | 値 |
|---|---|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key |

### ローカル（手動実行用・任意）

`.env` に追記:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

設定後、`./run.sh` か Actions の手動実行で1回流すと初日のデータが入る。

## 3. Vercel デプロイ

1. https://vercel.com → Add New Project → このリポジトリを import
2. **Root Directory を `dashboard` に設定**（重要）
3. Environment Variables に追加:

| 変数名 | 値 |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon key |

4. Deploy。以降 main への push で自動デプロイ。

> anon キーは RLS により**読み取り専用**（`storage/schema.sql` で public read ポリシーのみ付与、書き込みは service_role のみ）。

## 4. 動作確認

- エージェント実行後、Supabase Table Editor で `market_snapshots` に行が入っていること
- ダッシュボード URL を開いて DEMO DATA バッジが**消えている**こと
- スパークラインは履歴が2日分以上溜まると表示される

## ローカル開発

```bash
cd dashboard
pnpm install
pnpm dev   # http://localhost:3000 （キー未設定ならデモデータ）
```
