import type {
  CalendarRow,
  DashboardData,
  MarketRow,
  NewsRow,
  SummaryRow,
} from "./types";
import { MOCK_DATA } from "./mock";

const PROJECT_ID = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
const API_KEY = process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
const REVALIDATE_SEC = 300;
const HISTORY_DAYS = 31;

// Firestore REST API の型付き値表現
type FsValue = {
  stringValue?: string;
  integerValue?: string;
  doubleValue?: number;
  booleanValue?: boolean;
  nullValue?: null;
  timestampValue?: string;
  arrayValue?: { values?: FsValue[] };
  mapValue?: { fields?: Record<string, FsValue> };
};

function decode(v: FsValue): unknown {
  if (v.stringValue !== undefined) return v.stringValue;
  if (v.integerValue !== undefined) return Number(v.integerValue);
  if (v.doubleValue !== undefined) return v.doubleValue;
  if (v.booleanValue !== undefined) return v.booleanValue;
  if (v.timestampValue !== undefined) return v.timestampValue;
  if (v.arrayValue !== undefined)
    return (v.arrayValue.values ?? []).map(decode);
  if (v.mapValue !== undefined)
    return Object.fromEntries(
      Object.entries(v.mapValue.fields ?? {}).map(([k, f]) => [k, decode(f)]),
    );
  return null;
}

interface ReportDoc {
  snapshot_date: string;
  market: Omit<MarketRow, "snapshot_date">[];
  news: Omit<NewsRow, "snapshot_date">[];
  calendar: Omit<CalendarRow, "snapshot_date">[];
  summary: Omit<SummaryRow, "snapshot_date"> | null;
}

async function fetchRecentReports(limit: number): Promise<ReportDoc[]> {
  const url =
    `https://firestore.googleapis.com/v1/projects/${PROJECT_ID}` +
    `/databases/(default)/documents:runQuery?key=${API_KEY}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      structuredQuery: {
        from: [{ collectionId: "daily_reports" }],
        orderBy: [
          { field: { fieldPath: "snapshot_date" }, direction: "DESCENDING" },
        ],
        limit,
      },
    }),
    next: { revalidate: REVALIDATE_SEC },
  });
  if (!res.ok) {
    throw new Error(`Firestore query failed (${res.status})`);
  }
  const rows: { document?: { fields: Record<string, FsValue> } }[] =
    await res.json();
  return rows
    .filter((r) => r.document)
    .map(
      (r) =>
        Object.fromEntries(
          Object.entries(r.document!.fields).map(([k, v]) => [k, decode(v)]),
        ) as unknown as ReportDoc,
    );
}

function withDate<T>(rows: T[], date: string): (T & { snapshot_date: string })[] {
  return rows.map((r) => ({ ...r, snapshot_date: date }));
}

export async function getDashboardData(): Promise<DashboardData> {
  if (!PROJECT_ID || !API_KEY) return MOCK_DATA;

  const reports = await fetchRecentReports(HISTORY_DAYS);
  const latest = reports[0];
  if (!latest) return { ...MOCK_DATA, isDemo: true };

  // スパークライン用: 過去レポートから個別株の価格履歴を抽出（古い順）
  const history: MarketRow[] = [...reports]
    .reverse()
    .flatMap((rep) =>
      withDate(
        rep.market.filter(
          (m) => m.category === "us_stock" || m.category === "jp_stock",
        ),
        rep.snapshot_date,
      ),
    );

  return {
    isDemo: false,
    snapshotDate: latest.snapshot_date,
    market: withDate(latest.market, latest.snapshot_date),
    history,
    news: withDate(latest.news, latest.snapshot_date),
    calendar: withDate(latest.calendar, latest.snapshot_date),
    summary: latest.summary
      ? { ...latest.summary, snapshot_date: latest.snapshot_date }
      : null,
  };
}
