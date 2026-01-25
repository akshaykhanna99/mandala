"use client";

type SourceRef = {
  name: string;
  url: string;
};

export type FeedItem = {
  id: string;
  country: string;
  countryId: string;
  countries: string[];
  countryIds: string[];
  activity: string;
  title: string;
  summary: string;
  updatedAt: string;
  sources: SourceRef[];
  isGlobal: boolean;
  topic: string;
};

type SignalsFeedProps = {
  feedTab: "news" | "socials";
  onChangeTab: (tab: "news" | "socials") => void;
  feedQuery: string;
  onChangeQuery: (value: string) => void;
  lastUpdated: string;
  showFilters: boolean;
  onShowFilters: (value: boolean) => void;
  feedCountry: string;
  onChangeCountry: (value: string) => void;
  feedOutlet: string;
  onChangeOutlet: (value: string) => void;
  feedTopic: string;
  onChangeTopic: (value: string) => void;
  feedRangeDays: number;
  onChangeRangeDays: (value: number) => void;
  countriesList: string[];
  outletsList: string[];
  topicsList: string[];
  feedItems: FeedItem[];
  getStatusStyle: (status?: string) => string;
  truncateText: (text: string, maxLength: number) => string;
  onClose: () => void;
};

export default function SignalsFeed({
  feedTab,
  onChangeTab,
  feedQuery,
  onChangeQuery,
  lastUpdated,
  showFilters,
  onShowFilters,
  feedCountry,
  onChangeCountry,
  feedOutlet,
  onChangeOutlet,
  feedTopic,
  onChangeTopic,
  feedRangeDays,
  onChangeRangeDays,
  countriesList,
  outletsList,
  topicsList,
  feedItems,
  getStatusStyle,
  truncateText,
  onClose,
}: SignalsFeedProps) {
  return (
    <aside className="pointer-events-auto absolute left-8 top-24 bottom-6 w-[360px] overflow-hidden rounded-[28px] border border-white/10 bg-black/40 shadow-[0_24px_80px_rgba(10,10,10,0.35)] backdrop-blur">
      <div className="flex h-full flex-col">
        <div className="border-b border-white/10 px-5 py-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">
                Signals feed
              </p>
              {lastUpdated ? (
                <p className="mt-1 text-[10px] uppercase tracking-[0.2em] text-white/40">
                  Updated {lastUpdated}
                </p>
              ) : null}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-white/15 text-white/70 transition hover:text-white"
              aria-label="Close signals feed"
              title="Close signals feed"
            >
              <svg
                viewBox="0 0 24 24"
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M6 6l12 12" />
                <path d="M18 6l-12 12" />
              </svg>
            </button>
          </div>
          <div className="mt-4 flex items-center gap-2">
            {(
              [
                { id: "news", label: "News" },
                { id: "socials", label: "Socials" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => onChangeTab(tab.id)}
                className={`rounded-full px-3 py-1 text-[10px] uppercase tracking-[0.2em] transition ${
                  feedTab === tab.id
                    ? "bg-white/15 text-white"
                    : "border border-white/15 text-white/60 hover:text-white"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="mt-4 flex items-center gap-2">
            <input
              value={feedQuery}
              onChange={(event) => onChangeQuery(event.target.value)}
              placeholder="Search keywords"
              className="w-full rounded-2xl border border-white/15 bg-black/30 px-4 py-2 text-sm text-white/80 placeholder:text-white/40 focus:border-white/30 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => onShowFilters(true)}
              className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/15 bg-black/30 text-white/70 transition hover:text-white"
              aria-label="Open filters"
              title="Open filters"
            >
              <svg
                viewBox="0 0 24 24"
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M4 6h16" />
                <path d="M7 12h10" />
                <path d="M10 18h4" />
              </svg>
            </button>
          </div>
          {showFilters ? (
            <div
              className="fixed inset-0 z-30 flex items-center justify-center bg-black/50 px-4"
              onClick={() => onShowFilters(false)}
            >
              <div
                className="w-full max-w-sm rounded-3xl border border-white/15 bg-[#0b0b0b] p-6 text-white/80 shadow-[0_24px_80px_rgba(0,0,0,0.5)]"
                onClick={(event) => event.stopPropagation()}
              >
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.3em] text-white/60">Filters</p>
                  <button
                    type="button"
                    onClick={() => onShowFilters(false)}
                    className="rounded-full border border-white/10 px-3 py-1 text-[10px] uppercase tracking-[0.2em] text-white/60 hover:text-white"
                  >
                    Close
                  </button>
                </div>
                <div className="mt-5 flex flex-col gap-3">
                  <select
                    value={feedCountry}
                    onChange={(event) => onChangeCountry(event.target.value)}
                    className="w-full rounded-2xl border border-white/15 bg-black/30 px-4 py-2 text-sm text-white/80 focus:border-white/30 focus:outline-none"
                  >
                    <option value="All">Country</option>
                    {countriesList
                      .filter((country) => country !== "All")
                      .map((country) => (
                        <option key={country} value={country}>
                          {country}
                        </option>
                      ))}
                  </select>
                  <select
                    value={feedOutlet}
                    onChange={(event) => onChangeOutlet(event.target.value)}
                    className="w-full rounded-2xl border border-white/15 bg-black/30 px-4 py-2 text-sm text-white/80 focus:border-white/30 focus:outline-none"
                  >
                    <option value="All">Outlet</option>
                    {outletsList
                      .filter((outlet) => outlet !== "All")
                      .map((outlet) => (
                        <option key={outlet} value={outlet}>
                          {outlet}
                        </option>
                      ))}
                  </select>
                  <select
                    value={feedTopic}
                    onChange={(event) => onChangeTopic(event.target.value)}
                    className="w-full rounded-2xl border border-white/15 bg-black/30 px-4 py-2 text-sm text-white/80 focus:border-white/30 focus:outline-none"
                  >
                    <option value="All">Topic</option>
                    {topicsList
                      .filter((topic) => topic !== "All")
                      .map((topic) => (
                        <option key={topic} value={topic}>
                          {topic === "country" ? "Country signals" : topic}
                        </option>
                      ))}
                  </select>
                  <select
                    value={feedRangeDays}
                    onChange={(event) => onChangeRangeDays(Number(event.target.value))}
                    className="w-full rounded-2xl border border-white/15 bg-black/30 px-4 py-2 text-sm text-white/80 focus:border-white/30 focus:outline-none"
                  >
                    <option value={1}>Last 24 hours</option>
                    <option value={7}>Last 7 days</option>
                  </select>
                </div>
              </div>
            </div>
          ) : null}
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-5">
          <div className="flex flex-col gap-4">
            {feedTab === "socials" ? (
              <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-white/60">
                Socials feed is not connected yet.
              </div>
            ) : (
              <>
                {feedItems.length === 0 ? (
                  <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-white/60">
                    No signals match the current filters.
                  </div>
                ) : null}
                {feedItems.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-3xl border border-white/10 bg-black/30 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.3em] text-white/50">
                          {item.country}
                        </p>
                        <h3 className="mt-2 text-sm font-semibold text-white/90">
                          {item.title}
                        </h3>
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.2em] ${getStatusStyle(
                          item.activity,
                        )}`}
                      >
                        {item.activity}
                      </span>
                    </div>
                    {item.summary ? (
                      <p className="mt-3 text-xs text-white/70">
                        {truncateText(item.summary, 160)}
                      </p>
                    ) : null}
                    <div className="mt-4 flex flex-wrap items-center gap-2 text-[10px] text-white/50">
                      {item.sources.map((source, index) => (
                        <a
                          key={`${item.id}-${source.name}-${source.url}-${index}`}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded-full border border-white/10 px-2 py-1 transition hover:border-white/30"
                        >
                          {source.name}
                        </a>
                      ))}
                      <span className="ml-auto text-[10px] uppercase tracking-[0.2em] text-white/40">
                        {item.updatedAt}
                      </span>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
