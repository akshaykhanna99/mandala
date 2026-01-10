"use client";

type MarketItem = {
  id: string;
  name: string;
  symbol: string;
  category: string;
  price: number;
  change?: number | null;
  change_pct?: number | null;
  updated_at: string;
  source: string;
};

type MarketsFeedProps = {
  items: MarketItem[];
};

const formatNumber = (value: number) =>
  value >= 100 ? value.toFixed(2) : value.toFixed(3);

export default function MarketsFeed({ items }: MarketsFeedProps) {
  const rendered = items.length
    ? items
    : [
        {
          id: "empty",
          name: "Markets",
          symbol: "—",
          category: "Awaiting data",
          price: 0,
          change_pct: null,
          updated_at: "",
          source: "",
        },
      ];
  return (
    <div className="pointer-events-none absolute bottom-6 left-6 right-6">
      <div className="pointer-events-auto overflow-hidden rounded-full border border-white/10 bg-black/50 px-6 py-3 shadow-[0_24px_80px_rgba(10,10,10,0.35)] backdrop-blur">
        <div className="ticker-track">
          {[...rendered, ...rendered].map((item, index) => {
            const changePct =
              typeof item.change_pct === "number"
                ? `${item.change_pct > 0 ? "+" : ""}${item.change_pct.toFixed(2)}%`
                : "—";
            const changeColor =
              typeof item.change_pct === "number"
                ? item.change_pct >= 0
                  ? "text-emerald-300"
                  : "text-rose-300"
                : "text-white/60";
            return (
              <div
                key={`${item.id}-${index}`}
                className="flex items-center gap-3 whitespace-nowrap px-4 text-xs text-white/80"
              >
                <span className="text-white/50">{item.symbol}</span>
                <span className="font-semibold text-white">{formatNumber(item.price)}</span>
                <span className={changeColor}>{changePct}</span>
                <span className="text-[10px] uppercase tracking-[0.2em] text-white/40">
                  {item.name}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
