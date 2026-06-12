const WIDTH = 96;
const HEIGHT = 28;
const PAD = 2;

export function Sparkline({
  prices,
  positive,
}: {
  prices: number[];
  positive: boolean;
}) {
  if (prices.length < 2) {
    return <span style={{ color: "var(--text-low)" }}>–</span>;
  }
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const step = (WIDTH - PAD * 2) / (prices.length - 1);
  const points = prices
    .map((p, i) => {
      const x = PAD + i * step;
      const y = HEIGHT - PAD - ((p - min) / range) * (HEIGHT - PAD * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const color = positive ? "var(--up)" : "var(--down)";

  return (
    <svg
      width={WIDTH}
      height={HEIGHT}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label="30日間の価格推移"
    >
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        opacity="0.9"
      />
    </svg>
  );
}
