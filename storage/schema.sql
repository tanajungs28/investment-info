-- 投資情報エージェント Phase 3: Supabase スキーマ
-- Supabase SQL Editor で一度実行する。

create table if not exists market_snapshots (
  id bigint generated always as identity primary key,
  snapshot_date date not null,
  category text not null check (category in
    ('index', 'forex', 'us_stock', 'jp_stock', 'us_sector', 'jp_sector')),
  ticker text not null,
  name text not null,
  price numeric not null,
  change_pct numeric not null,
  volume bigint,
  avg_volume bigint,
  created_at timestamptz not null default now(),
  unique (snapshot_date, ticker)
);

create table if not exists news_items (
  id bigint generated always as identity primary key,
  snapshot_date date not null,
  title text not null,
  url text not null default '',
  source text,
  published timestamptz,
  tickers text[] not null default '{}',
  created_at timestamptz not null default now(),
  unique (snapshot_date, url)
);

create table if not exists calendar_events (
  id bigint generated always as identity primary key,
  snapshot_date date not null,
  time text not null,
  currency text not null,
  title text not null,
  importance int not null,
  created_at timestamptz not null default now(),
  unique (snapshot_date, time, currency, title)
);

create table if not exists daily_summaries (
  snapshot_date date primary key,
  key_points text[] not null default '{}',
  mover_explanations jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists idx_market_snapshots_ticker_date
  on market_snapshots (ticker, snapshot_date desc);
create index if not exists idx_news_items_date
  on news_items (snapshot_date desc);

-- RLS: 匿名キーは読み取り専用。書き込みは service_role キー（RLSをバイパス）のみ。
alter table market_snapshots enable row level security;
alter table news_items enable row level security;
alter table calendar_events enable row level security;
alter table daily_summaries enable row level security;

create policy "public read" on market_snapshots for select using (true);
create policy "public read" on news_items for select using (true);
create policy "public read" on calendar_events for select using (true);
create policy "public read" on daily_summaries for select using (true);
