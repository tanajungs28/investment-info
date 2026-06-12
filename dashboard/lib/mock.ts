import type { DashboardData, MarketRow } from "./types";

// Supabase 未設定時に UI を確認するためのデモデータ。
// 値はダミーであり実勢を反映しない。

const DATE = "2026-06-12";

function stock(
  category: MarketRow["category"],
  ticker: string,
  name: string,
  price: number,
  changePct: number,
  volume?: number,
  avgVolume?: number,
): MarketRow {
  return {
    snapshot_date: DATE,
    category,
    ticker,
    name,
    price,
    change_pct: changePct,
    volume: volume ?? null,
    avg_volume: avgVolume ?? null,
  };
}

const market: MarketRow[] = [
  stock("index", "^GSPC", "S&P 500", 6712.4, 0.82),
  stock("index", "^IXIC", "NASDAQ", 21840.9, 1.21),
  stock("index", "^DJI", "Dow Jones", 46871.2, -0.15),
  stock("index", "^N225", "日経225", 66124.5, 2.31),
  stock("index", "1306.T", "TOPIX", 4231.8, 1.88),
  stock("forex", "JPY=X", "USD/JPY", 151.42, -0.35),
  stock("forex", "EURUSD=X", "EUR/USD", 1.114, 0.12),
  stock("us_stock", "NVDA", "NVIDIA", 1242.1, 3.21, 52_000_000, 24_000_000),
  stock("us_stock", "AAPL", "Apple", 248.6, 0.42, 41_000_000, 48_000_000),
  stock("us_stock", "MSFT", "Microsoft", 512.3, -0.88, 18_000_000, 21_000_000),
  stock("us_stock", "MU", "Micron Technology", 168.4, -2.1, 33_000_000, 19_000_000),
  stock("us_stock", "WDC", "Western Digital", 92.7, 4.5, 28_000_000, 9_000_000),
  stock("us_stock", "MO", "Altria Group", 58.2, 0.3, 6_000_000, 7_000_000),
  stock("jp_stock", "7203.T", "トヨタ自動車", 3412, 1.5, 21_000_000, 18_000_000),
  stock("jp_stock", "6758.T", "ソニーグループ", 15820, -1.2, 8_400_000, 6_100_000),
  stock("jp_stock", "9984.T", "ソフトバンクグループ", 12440, 3.8, 14_000_000, 5_200_000),
  stock("jp_stock", "8035.T", "東京エレクトロン", 31250, 2.2, 4_100_000, 3_900_000),
  stock("us_sector", "XLK", "テクノロジー", 0, 1.4),
  stock("us_sector", "XLC", "コミュニケーション", 0, 0.9),
  stock("us_sector", "XLY", "一般消費財", 0, 0.5),
  stock("us_sector", "XLP", "生活必需品", 0, -0.2),
  stock("us_sector", "XLV", "ヘルスケア", 0, 0.6),
  stock("us_sector", "XLF", "金融", 0, 0.3),
  stock("us_sector", "XLI", "資本財", 0, -0.4),
  stock("us_sector", "XLB", "素材", 0, -0.7),
  stock("us_sector", "XLRE", "不動産", 0, 0.1),
  stock("us_sector", "XLU", "公益事業", 0, -0.1),
  stock("us_sector", "XLE", "エネルギー", 0, -1.6),
  stock("jp_sector", "1615.T", "銀行業", 0, 1.1),
  stock("jp_sector", "1617.T", "食料品", 0, 0.2),
  stock("jp_sector", "1620.T", "化学", 0, 0.8),
  stock("jp_sector", "1621.T", "医薬品", 0, -0.5),
  stock("jp_sector", "1622.T", "輸送用機器", 0, 1.9),
  stock("jp_sector", "1625.T", "電気機器", 0, 2.4),
  stock("jp_sector", "1626.T", "情報・通信業", 0, 1.2),
  stock("jp_sector", "1628.T", "不動産業", 0, -0.9),
];

// スパークライン用の30日ダミー履歴
function demoHistory(): MarketRow[] {
  const rows: MarketRow[] = [];
  const tickers = market.filter(
    (m) => m.category === "us_stock" || m.category === "jp_stock",
  );
  for (const base of tickers) {
    let price = base.price * 0.9;
    for (let i = 29; i >= 0; i--) {
      const d = new Date(2026, 5, 12);
      d.setDate(d.getDate() - i);
      const wobble = Math.sin((i + base.ticker.length) * 0.9) * 0.012;
      price = price * (1 + wobble + 0.0035);
      rows.push({
        ...base,
        snapshot_date: d.toISOString().slice(0, 10),
        price: Math.round(price * 100) / 100,
      });
    }
  }
  return rows;
}

export const MOCK_DATA: DashboardData = {
  isDemo: true,
  snapshotDate: DATE,
  market,
  history: demoHistory(),
  news: [
    {
      snapshot_date: DATE,
      title: "エヌビディア、次世代GPUの量産前倒しを発表",
      url: "https://example.com/nvda",
      source: "日経 マーケット",
      published: `${DATE}T22:10:00Z`,
      tickers: ["NVDA"],
    },
    {
      snapshot_date: DATE,
      title: "ソフトバンクG、AIデータセンターへ追加投資",
      url: "https://example.com/sbg",
      source: "Yahoo!ニュース 経済",
      published: `${DATE}T21:40:00Z`,
      tickers: ["9984.T"],
    },
    {
      snapshot_date: DATE,
      title: "トヨタ、北米販売が過去最高を更新",
      url: "https://example.com/toyota",
      source: "NHK 経済",
      published: `${DATE}T20:15:00Z`,
      tickers: ["7203.T"],
    },
    {
      snapshot_date: DATE,
      title: "米CPI発表を前に様子見ムード広がる",
      url: "https://example.com/cpi",
      source: "Yahoo!ニュース 経済",
      published: `${DATE}T19:00:00Z`,
      tickers: [],
    },
  ],
  calendar: [
    { snapshot_date: DATE, time: "21:30", currency: "USD", title: "消費者物価指数 (CPI)", importance: 3 },
    { snapshot_date: DATE, time: "27:00", currency: "USD", title: "FOMC議事録公表", importance: 3 },
    { snapshot_date: DATE, time: "08:50", currency: "JPY", title: "日銀短観", importance: 2 },
  ],
  summary: {
    snapshot_date: DATE,
    key_points: [
      "① 米CPIの結果次第でFRBの利下げ観測が大きく動く可能性。",
      "② NVDA・WDCは出来高急増を伴う上昇でモメンタム継続に注目。",
      "③ 円高一服なら輸出株（トヨタ・東エレク）の押し目が機能しやすい。",
    ],
    mover_explanations: {
      NVDA: "次世代GPU量産前倒し報道を受けて買いが集中。",
      "9984.T": "AIデータセンター追加投資の発表を好感。",
    },
  },
};
