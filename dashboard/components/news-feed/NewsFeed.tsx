import Link from "next/link";
import type { NewsRow } from "@/lib/types";
import styles from "./news-feed.module.css";

function timeOf(published: string | null): string {
  if (!published) return "";
  return new Date(published).toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Tokyo",
  });
}

export function NewsFeed({
  news,
  activeTicker,
}: {
  news: NewsRow[];
  activeTicker: string | null;
}) {
  const tickers = [...new Set(news.flatMap((n) => n.tickers))].sort();
  const filtered = activeTicker
    ? news.filter((n) => n.tickers.includes(activeTicker))
    : news;

  return (
    <section className="card" aria-label="ニュースフィード">
      <h2 className="card-title">ニュース</h2>

      {tickers.length > 0 && (
        <nav className={styles.filters} aria-label="銘柄フィルタ">
          <Link
            href="/"
            className={!activeTicker ? styles.chipActive : styles.chip}
            scroll={false}
          >
            すべて
          </Link>
          {tickers.map((t) => (
            <Link
              key={t}
              href={`/?ticker=${encodeURIComponent(t)}`}
              className={activeTicker === t ? styles.chipActive : styles.chip}
              scroll={false}
            >
              {t}
            </Link>
          ))}
        </nav>
      )}

      <ul className={styles.list}>
        {filtered.length === 0 && (
          <li className={styles.empty}>該当するニュースはありません</li>
        )}
        {filtered.map((n) => (
          <li key={`${n.url}-${n.title}`} className={styles.item}>
            <div className={styles.meta}>
              <span className={`num ${styles.time}`}>{timeOf(n.published)}</span>
              {n.tickers.map((t) => (
                <span key={t} className={styles.tag}>
                  {t}
                </span>
              ))}
              <span className={styles.source}>{n.source}</span>
            </div>
            {n.url ? (
              <a
                href={n.url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.title}
              >
                {n.title}
              </a>
            ) : (
              <span className={styles.title}>{n.title}</span>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
