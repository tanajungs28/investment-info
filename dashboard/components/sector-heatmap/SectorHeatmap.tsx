import type { MarketRow } from "@/lib/types";
import styles from "./sector-heatmap.module.css";

function pct(v: number): string {
  return `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function tileStyle(changePct: number, maxAbs: number): React.CSSProperties {
  const intensity = Math.min(Math.abs(changePct) / (maxAbs || 1), 1);
  const alpha = 0.12 + intensity * 0.55;
  const color = changePct >= 0 ? "var(--up)" : "var(--down)";
  return {
    background: `color-mix(in oklch, ${color} ${Math.round(alpha * 100)}%, var(--surface-1))`,
  };
}

function Grid({ label, sectors }: { label: string; sectors: MarketRow[] }) {
  const ranked = [...sectors].sort((a, b) => b.change_pct - a.change_pct);
  const maxAbs = Math.max(...ranked.map((s) => Math.abs(s.change_pct)), 0);
  return (
    <div>
      <h3 className={styles.regionLabel}>{label}</h3>
      <ul className={styles.grid}>
        {ranked.map((s) => (
          <li
            key={s.ticker}
            className={styles.tile}
            style={tileStyle(s.change_pct, maxAbs)}
          >
            <span className={styles.sectorName}>{s.name}</span>
            <span className={`num ${styles.sectorPct}`}>{pct(s.change_pct)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function SectorHeatmap({
  usSectors,
  jpSectors,
}: {
  usSectors: MarketRow[];
  jpSectors: MarketRow[];
}) {
  return (
    <section className="card" aria-label="セクターヒートマップ">
      <h2 className="card-title">セクターヒートマップ</h2>
      <div className={styles.regions}>
        {usSectors.length > 0 && <Grid label="米国" sectors={usSectors} />}
        {jpSectors.length > 0 && <Grid label="日本" sectors={jpSectors} />}
      </div>
    </section>
  );
}
