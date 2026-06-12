export type MarketCategory =
  | "index"
  | "forex"
  | "us_stock"
  | "jp_stock"
  | "us_sector"
  | "jp_sector";

export interface MarketRow {
  snapshot_date: string;
  category: MarketCategory;
  ticker: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number | null;
  avg_volume: number | null;
}

export interface NewsRow {
  snapshot_date: string;
  title: string;
  url: string;
  source: string | null;
  published: string | null;
  tickers: string[];
}

export interface CalendarRow {
  snapshot_date: string;
  time: string;
  currency: string;
  title: string;
  importance: number;
}

export interface SummaryRow {
  snapshot_date: string;
  key_points: string[];
  mover_explanations: Record<string, string>;
}

export interface DashboardData {
  isDemo: boolean;
  snapshotDate: string;
  market: MarketRow[];
  history: MarketRow[];
  news: NewsRow[];
  calendar: CalendarRow[];
  summary: SummaryRow | null;
}

export function volumeRatio(row: MarketRow): number | null {
  if (!row.volume || !row.avg_volume) return null;
  return row.volume / row.avg_volume;
}
