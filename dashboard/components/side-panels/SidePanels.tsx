import type { CalendarRow, SummaryRow } from "@/lib/types";
import styles from "./side-panels.module.css";

const STARS: Record<number, string> = { 3: "★★★", 2: "★★☆", 1: "★☆☆" };

export function CalendarCard({ events }: { events: CalendarRow[] }) {
  return (
    <section className="card" aria-label="経済指標カレンダー">
      <h2 className="card-title">経済指標</h2>
      {events.length === 0 ? (
        <p className={styles.empty}>本日の重要指標はありません</p>
      ) : (
        <ul className={styles.calendar}>
          {events.map((e) => (
            <li key={`${e.time}-${e.currency}-${e.title}`} className={styles.event}>
              <span className={`num ${styles.time}`}>{e.time}</span>
              <span className={styles.currency}>{e.currency}</span>
              <span className={styles.eventTitle}>{e.title}</span>
              <span
                className={e.importance >= 3 ? styles.starsHigh : styles.stars}
                aria-label={`重要度${e.importance}`}
              >
                {STARS[e.importance] ?? ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function SummaryCard({ summary }: { summary: SummaryRow | null }) {
  return (
    <section className={`card ${styles.summaryCard}`} aria-label="今日の注目ポイント">
      <h2 className="card-title">今日の注目ポイント — Claude</h2>
      {!summary || summary.key_points.length === 0 ? (
        <p className={styles.empty}>要約はまだ生成されていません</p>
      ) : (
        <ol className={styles.points}>
          {summary.key_points.map((p) => (
            <li key={p}>{p.replace(/^[①②③]\s*/, "")}</li>
          ))}
        </ol>
      )}
    </section>
  );
}
