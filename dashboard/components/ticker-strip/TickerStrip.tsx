import type { MarketRow } from "@/lib/types";
import styles from "./ticker-strip.module.css";

function pct(v: number): string {
  return `${v > 0 ? "+" : ""}${v.toFixed(2)}%`;
}

export function TickerStrip({ rows }: { rows: MarketRow[] }) {
  return (
    <ul className={styles.strip} aria-label="指数・為替サマリー">
      {rows.map((r) => (
        <li key={r.ticker} className={styles.item}>
          <span className={styles.name}>{r.name}</span>
          <span className={`num ${styles.price}`}>
            {r.price.toLocaleString("ja-JP", { maximumFractionDigits: 2 })}
          </span>
          {r.category === "index" && (
            <span className={`num ${r.change_pct >= 0 ? "up" : "down"}`}>
              {pct(r.change_pct)}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
