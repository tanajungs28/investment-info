import type {
  CalendarRow,
  DashboardData,
  MarketRow,
  NewsRow,
  SummaryRow,
} from "./types";
import { MOCK_DATA } from "./mock";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const REVALIDATE_SEC = 300;
const HISTORY_DAYS = 30;

function isConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}

async function pg<T>(query: string): Promise<T> {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${query}`, {
    headers: {
      apikey: SUPABASE_ANON_KEY!,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    },
    next: { revalidate: REVALIDATE_SEC },
  });
  if (!res.ok) {
    throw new Error(`Supabase query failed (${res.status}): ${query}`);
  }
  return res.json() as Promise<T>;
}

async function latestSnapshotDate(): Promise<string | null> {
  const rows = await pg<{ snapshot_date: string }[]>(
    "market_snapshots?select=snapshot_date&order=snapshot_date.desc&limit=1",
  );
  return rows[0]?.snapshot_date ?? null;
}

export async function getDashboardData(): Promise<DashboardData> {
  if (!isConfigured()) return MOCK_DATA;

  const date = await latestSnapshotDate();
  if (!date) return { ...MOCK_DATA, isDemo: true };

  const since = new Date(date);
  since.setDate(since.getDate() - HISTORY_DAYS);
  const sinceStr = since.toISOString().slice(0, 10);

  const [market, history, news, calendar, summaries] = await Promise.all([
    pg<MarketRow[]>(`market_snapshots?snapshot_date=eq.${date}&select=*`),
    pg<MarketRow[]>(
      `market_snapshots?snapshot_date=gte.${sinceStr}` +
        `&category=in.(us_stock,jp_stock)&select=*&order=snapshot_date.asc`,
    ),
    pg<NewsRow[]>(
      `news_items?snapshot_date=eq.${date}&select=*&order=published.desc`,
    ),
    pg<CalendarRow[]>(
      `calendar_events?snapshot_date=eq.${date}&select=*&order=importance.desc`,
    ),
    pg<SummaryRow[]>(`daily_summaries?snapshot_date=eq.${date}&select=*`),
  ]);

  return {
    isDemo: false,
    snapshotDate: date,
    market,
    history,
    news,
    calendar,
    summary: summaries[0] ?? null,
  };
}
