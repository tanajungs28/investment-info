import type { MarketRow } from "@/lib/types";
import { volumeRatio } from "@/lib/types";
import { Sparkline } from "../sparkline/Sparkline";
import styles from "./watchlist-table.module.css";

const VOLUME_ALERT_RATIO = 2.0;

function pct(v: number): string {
  return `${v > 0 ? "+" : ""}${v.toFixed(2)}%`;
}

function Row({
  row,
  prices,
  explanation,
}: {
  row: MarketRow;
  prices: number[];
  explanation?: string;
}) {
  const ratio = volumeRatio(row);
  const dir = row.change_pct >= 0 ? "up" : "down";
  return (
    <>
      <tr>
        <td>
          <span className={`num ${styles.ticker}`}>{row.ticker}</span>
          <span className={styles.name}>{row.name}</span>
        </td>
        <td className={`num ${styles.right}`}>
          {row.price.toLocaleString("ja-JP", { maximumFractionDigits: 2 })}
        </td>
        <td className={`num ${styles.right} ${dir}`}>{pct(row.change_pct)}</td>
        <td className={`num ${styles.right}`}>
          {ratio !== null ? (
            <span className={ratio >= VOLUME_ALERT_RATIO ? styles.volAlert : undefined}>
              {ratio.toFixed(1)}×
            </span>
          ) : (
            <span className={styles.dim}>–</span>
          )}
        </td>
        <td className={styles.spark}>
          <Sparkline prices={prices} positive={row.change_pct >= 0} />
        </td>
      </tr>
      {explanation && (
        <tr className={styles.explainRow}>
          <td colSpan={5}>└ {explanation}</td>
        </tr>
      )}
    </>
  );
}

export function WatchlistTable({
  title,
  rows,
  history,
  explanations,
}: {
  title: string;
  rows: MarketRow[];
  history: MarketRow[];
  explanations: Record<string, string>;
}) {
  const sorted = [...rows].sort(
    (a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct),
  );
  const pricesFor = (ticker: string) =>
    history.filter((h) => h.ticker === ticker).map((h) => h.price);

  return (
    <section className="card" aria-label={title}>
      <h2 className="card-title">{title}</h2>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>銘柄</th>
            <th className={styles.right}>価格</th>
            <th className={styles.right}>前日比</th>
            <th className={styles.right}>出来高比</th>
            <th>30日</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <Row
              key={row.ticker}
              row={row}
              prices={pricesFor(row.ticker)}
              explanation={explanations[row.ticker]}
            />
          ))}
        </tbody>
      </table>
    </section>
  );
}
