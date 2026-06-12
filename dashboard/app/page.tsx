import { getDashboardData } from "@/lib/data";
import { TickerStrip } from "@/components/ticker-strip/TickerStrip";
import { WatchlistTable } from "@/components/watchlist-table/WatchlistTable";
import { SectorHeatmap } from "@/components/sector-heatmap/SectorHeatmap";
import { NewsFeed } from "@/components/news-feed/NewsFeed";
import { CalendarCard, SummaryCard } from "@/components/side-panels/SidePanels";
import styles from "./page.module.css";

export const revalidate = 300;

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ ticker?: string }>;
}) {
  const { ticker } = await searchParams;
  const data = await getDashboardData();
  const by = (cat: string) => data.market.filter((m) => m.category === cat);
  const dateLabel = new Date(`${data.snapshotDate}T00:00:00`).toLocaleDateString(
    "ja-JP",
    { year: "numeric", month: "long", day: "numeric", weekday: "short" },
  );

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.kicker}>MORNING TERMINAL</p>
          <h1 className={styles.title}>
            {dateLabel}
            <span className={styles.titleSub}>の市況</span>
          </h1>
        </div>
        {data.isDemo && (
          <span className={styles.demoBadge} title="Supabase 未接続のためサンプルデータを表示中">
            DEMO DATA
          </span>
        )}
      </header>

      <TickerStrip rows={[...by("index"), ...by("forex")]} />

      <div className={styles.grid}>
        <div className={styles.mainCol}>
          <WatchlistTable
            title="米国株ウォッチリスト"
            rows={by("us_stock")}
            history={data.history}
            explanations={data.summary?.mover_explanations ?? {}}
          />
          <WatchlistTable
            title="日本株ウォッチリスト"
            rows={by("jp_stock")}
            history={data.history}
            explanations={data.summary?.mover_explanations ?? {}}
          />
        </div>
        <div className={styles.sideCol}>
          <SummaryCard summary={data.summary} />
          <CalendarCard events={data.calendar} />
        </div>
      </div>

      <SectorHeatmap usSectors={by("us_sector")} jpSectors={by("jp_sector")} />

      <NewsFeed news={data.news} activeTicker={ticker ?? null} />

      <footer className={styles.footer}>
        毎朝 6:00 JST に自動更新 ・ データ: Yahoo Finance / Yahoo!ニュース / NHK /
        日経 / Forex Factory ・ 要約: Claude
      </footer>
    </main>
  );
}
