import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Morning Terminal | 投資情報ダッシュボード",
  description:
    "日米株式市場のウォッチリスト・セクター動向・ニュース・経済指標を毎朝自動更新するダッシュボード",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
