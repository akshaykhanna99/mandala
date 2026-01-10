"use client";

import ControlBar from "@/components/ControlBar";
import ChatPanel from "@/components/ChatPanel";
import MarketsFeed from "@/components/MarketsFeed";
import MapView, { type AirTrafficPoint, type NewsPin } from "@/components/MapView";
import SignalsFeed, { type FeedItem } from "@/components/SignalsFeed";
import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";

type SourceRef = {
  name: string;
  url: string;
};

type EventCluster = {
  title: string;
  summary: string;
  why: string;
  confidence: string;
  sources: SourceRef[];
  updated_at: string;
};

type GlobalItem = {
  title: string;
  summary: string;
  source: SourceRef;
  url: string;
  published_at: string;
  topic: string;
  countries: string[];
  country_ids: string[];
};

type CountrySnapshot = {
  id: string;
  name: string;
  activity_level: string;
  updated_at: string;
  events: EventCluster[];
  stats: {
    signals: number;
    disputes: number;
    confidence: number;
  };
};

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

type NotamItem = {
  id: string;
  location: string;
  issued_at: string;
  summary: string;
  source: string;
  updated_at: string;
};

export default function Home() {
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [hoverPosition, setHoverPosition] = useState<{ x: number; y: number } | null>(
    null,
  );
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [hoverPin, setHoverPin] = useState<NewsPin | null>(null);
  const [showLabels, setShowLabels] = useState(true);
  const [showCapitals, setShowCapitals] = useState(true);
  const [showAirTraffic, setShowAirTraffic] = useState(false);
  const [feedQuery, setFeedQuery] = useState("");
  const [feedCountry, setFeedCountry] = useState("All");
  const [feedOutlet, setFeedOutlet] = useState("All");
  const [feedTopic, setFeedTopic] = useState("All");
  const [feedRangeDays, setFeedRangeDays] = useState(1);
  const [showFeedFilters, setShowFeedFilters] = useState(false);
  const [showSignals, setShowSignals] = useState(true);
  const [showAgent, setShowAgent] = useState(true);
  const [feedTab, setFeedTab] = useState<"news" | "notams" | "socials">("news");
  const [favoriteCountries, setFavoriteCountries] = useState<string[]>([]);
  const [globalItems, setGlobalItems] = useState<GlobalItem[]>([]);
  const [snapshots, setSnapshots] = useState<Record<string, CountrySnapshot>>({});
  const [marketItems, setMarketItems] = useState<MarketItem[]>([]);
  const [airTraffic, setAirTraffic] = useState<AirTrafficPoint[]>([]);
  const [notams, setNotams] = useState<NotamItem[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastSignalsUpdate, setLastSignalsUpdate] = useState<string>("");
  const [agentMessages, setAgentMessages] = useState<
    { role: "user" | "assistant"; content: string }[]
  >([]);
  const [isAgentSending, setIsAgentSending] = useState(false);
  const focusPanelRef = useRef<HTMLDivElement | null>(null);
  const refreshGroupRef = useRef<HTMLDivElement | null>(null);
  const suppressClearRef = useRef(false);

  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://localhost:8000";

  const loadSnapshots = async () => {
    try {
      const response = await fetch(`${apiBase}/countries`);
      if (!response.ok) {
        throw new Error("Failed to fetch snapshots");
      }
      const data: CountrySnapshot[] = await response.json();
      const map: Record<string, CountrySnapshot> = {};
      data.forEach((item) => {
        if (item.id) {
          map[item.id] = item;
        }
      });
      setSnapshots(map);
    } catch (error) {
      console.error(error);
    }
  };

  const loadGlobalItems = async () => {
    try {
      const response = await fetch(`${apiBase}/global`);
      if (!response.ok) {
        throw new Error("Failed to fetch global feed");
      }
      const data: GlobalItem[] = await response.json();
      setGlobalItems(data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetch(`${apiBase}/refresh?days=${feedRangeDays}`, { method: "POST" });
      await Promise.all([
        loadSnapshots(),
        loadGlobalItems(),
        loadMarketItems(),
        loadNotams(),
      ]);
      setLastSignalsUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error(error);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadSnapshots();
    loadGlobalItems();
    loadMarketItems();
    loadNotams();
    setLastSignalsUpdate(new Date().toLocaleTimeString());
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => {
      handleRefresh();
    }, 15 * 60 * 1000);
    return () => window.clearInterval(interval);
  }, [feedRangeDays]);

  const loadMarketItems = async () => {
    try {
      const response = await fetch(`${apiBase}/markets`);
      if (!response.ok) {
        throw new Error("Failed to fetch markets");
      }
      const data: MarketItem[] = await response.json();
      setMarketItems(data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadNotams = async () => {
    try {
      const response = await fetch(`${apiBase}/notams`);
      if (!response.ok) {
        throw new Error("Failed to fetch NOTAMs");
      }
      const data: NotamItem[] = await response.json();
      setNotams(data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleAgentSend = async (message: string) => {
    setAgentMessages((prev) => [...prev, { role: "user", content: message }]);
    setIsAgentSending(true);
    try {
      const response = await fetch(`${apiBase}/agent/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: message }),
      });
      if (!response.ok) {
        throw new Error("Agent request failed");
      }
      const data = await response.json();
      const answer = data.answer || "No response generated.";
      setAgentMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch (error) {
      console.error(error);
      setAgentMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, Chanakya is unavailable right now." },
      ]);
    } finally {
      setIsAgentSending(false);
    }
  };

  useEffect(() => {
    const handleDocumentClick = (event: MouseEvent) => {
      if (!selectedCountry || suppressClearRef.current) {
        return;
      }
      const target = event.target as Node | null;
      if (!target) {
        return;
      }
      if (focusPanelRef.current?.contains(target)) {
        return;
      }
      if (refreshGroupRef.current?.contains(target)) {
        return;
      }
      setSelectedCountry(null);
    };

    document.addEventListener("click", handleDocumentClick);
    return () => {
      document.removeEventListener("click", handleDocumentClick);
    };
  }, [selectedCountry]);

  const handleHover = (name: string | null) => {
    setHoveredCountry(name);
  };

  const handleSelect = (name: string | null) => {
    if (name) {
      suppressClearRef.current = true;
      setTimeout(() => {
        suppressClearRef.current = false;
      }, 0);
    }
    setSelectedCountry(name);
  };

  const hoverSnapshot = hoveredCountry ? snapshots[hoveredCountry] : null;
  const hoverEvent = hoverSnapshot?.events?.[0] ?? null;
  const hoverCopy = useMemo(() => {
    if (!hoveredCountry || !hoverEvent) {
      return null;
    }

    return {
      text: hoverEvent.summary?.trim() ?? "",
      timestamp: hoverEvent.updated_at?.trim() ?? "",
    };
  }, [hoveredCountry, hoverEvent]);

  const selectedSnapshot = selectedCountry ? snapshots[selectedCountry] : null;
  const selectedEvents = selectedSnapshot?.events ?? [];
  const hoveredStatus = hoverSnapshot?.activity_level ?? "Watching";

  const getStatusStyle = (status?: string) => {
    const value = status?.toLowerCase();
    if (value === "escalating") {
      return "bg-[#c45f3a]/35 text-white/90";
    }
    if (value === "active") {
      return "bg-[#c8a63a]/35 text-white/90";
    }
    if (value === "calm") {
      return "bg-[#3f7f9c]/35 text-white/90";
    }
    return "bg-white/15 text-white/70";
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) {
      return text;
    }
    return `${text.slice(0, maxLength - 1).trim()}…`;
  };

  const scoreSeverity = (title: string, summary: string, topic?: string) => {
    const text = `${title} ${summary}`.toLowerCase();
    const base: Record<string, number> = {
      security: 0.9,
      humanitarian: 0.8,
      economy: 0.7,
      energy: 0.65,
      diplomacy: 0.6,
      general: 0.5,
    };
    let score = base[topic ?? "general"] ?? 0.5;
    const spikes = [
      "attack",
      "strike",
      "killed",
      "missile",
      "airstrike",
      "bomb",
      "sanction",
      "troop",
      "escalation",
      "ceasefire",
      "mobilization",
      "coup",
    ];
    if (spikes.some((keyword) => text.includes(keyword))) {
      score += 0.15;
    }
    return Math.max(0.25, Math.min(1, score));
  };

  const pins = useMemo(() => {
    const byCountry = new Map<
      string,
      {
        count: number;
        pin: NewsPin;
      }
    >();
    globalItems.forEach((item, index) => {
      const severity = scoreSeverity(item.title, item.summary, item.topic);
      const countries = item.countries || [];
      const countryIds = item.country_ids || [];
      countries.slice(0, 3).forEach((country, countryIndex) => {
        const countryId = countryIds[countryIndex] ?? country;
        const id = `${countryId}-${index}-${item.title}`;
        const pin: NewsPin = {
          id,
          countryName: country,
          countryId,
          title: item.title,
          summary: item.summary,
          updatedAt: item.published_at,
          source: item.source.name,
          url: item.url,
          severity,
          count: 1,
        };
        const existing = byCountry.get(countryId);
        if (!existing) {
          byCountry.set(countryId, { count: 1, pin });
          return;
        }
        existing.count += 1;
        if (pin.severity > existing.pin.severity) {
          existing.pin = pin;
        }
      });
    });
    return Array.from(byCountry.values()).map(({ count, pin }) => ({
      ...pin,
      count,
    }));
  }, [globalItems]);

  const toggleFavorite = (country: string) => {
    setFavoriteCountries((prev) =>
      prev.includes(country) ? prev.filter((item) => item !== country) : [...prev, country],
    );
  };

  const feedItems: FeedItem[] = useMemo(() => {
    let items: FeedItem[] = [];
    if (feedTab === "news") {
      items = globalItems.map((item, index) => ({
        id: `${item.title}-${index}-${item.source?.name}`,
        country: item.countries?.[0] ?? "",
        countryId: item.country_ids?.[0] ?? "",
        countries: item.countries ?? [],
        countryIds: item.country_ids ?? [],
        activity: "Watching",
        title: item.title,
        summary: item.summary,
        updatedAt: item.published_at,
        sources: [item.source],
        isGlobal: true,
        topic: item.topic,
      }));
    }

    const query = feedQuery.trim().toLowerCase();
    const filtered = items.filter((item) => {
      if (
        feedCountry !== "All" &&
        !(item.countries || []).includes(feedCountry) &&
        item.country !== feedCountry
      ) {
        return false;
      }
      if (feedOutlet !== "All") {
        const outlet = item.sources[0]?.name;
        if (outlet !== feedOutlet) {
          return false;
        }
      }
      if (feedTopic !== "All" && item.topic !== feedTopic) {
        return false;
      }
      if (!query) {
        return true;
      }
      return (
        item.title.toLowerCase().includes(query) ||
        item.summary.toLowerCase().includes(query) ||
        item.country.toLowerCase().includes(query)
      );
    });

    const parseTime = (value: string) => {
      const parsed = Date.parse(value);
      return Number.isNaN(parsed) ? 0 : parsed;
    };

    return filtered.sort((a, b) => parseTime(b.updatedAt) - parseTime(a.updatedAt));
  }, [
    snapshots,
    globalItems,
    feedQuery,
    feedCountry,
    feedOutlet,
    feedTopic,
    feedTab,
  ]);

  const countriesList = useMemo(() => {
    const base = Object.values(snapshots).map((snapshot) => snapshot.name);
    const global = globalItems.flatMap((item) => item.countries || []);
    return ["All", ...Array.from(new Set([...base, ...global])).sort((a, b) => a.localeCompare(b))];
  }, [snapshots, globalItems]);

  const outletsList = useMemo(() => {
    const sources = feedItems
      .map((item) => item.sources[0]?.name)
      .filter((value): value is string => Boolean(value));
    return ["All", ...Array.from(new Set(sources)).sort((a, b) => a.localeCompare(b))];
  }, [feedItems]);

  const topicsList = useMemo(() => {
    const topics = feedItems
      .map((item) => item.topic)
      .filter((value): value is string => Boolean(value));
    return ["All", ...Array.from(new Set(topics)).sort((a, b) => a.localeCompare(b))];
  }, [feedItems]);

  const [viewport, setViewport] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const updateViewport = () => {
      setViewport({ width: window.innerWidth, height: window.innerHeight });
    };
    updateViewport();
    window.addEventListener("resize", updateViewport);
    return () => window.removeEventListener("resize", updateViewport);
  }, []);

  const loadAirTraffic = async () => {
    try {
      const response = await fetch(`${apiBase}/air-traffic`);
      if (!response.ok) {
        throw new Error("Failed to fetch air traffic");
      }
      const data: AirTrafficPoint[] = await response.json();
      setAirTraffic(data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    if (!showAirTraffic) {
      return;
    }
    let cancelled = false;
    const tick = async () => {
      if (!cancelled) {
        await loadAirTraffic();
      }
    };
    tick();
    const interval = window.setInterval(tick, 60000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [showAirTraffic]);

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0">
        <MapView
          onHoverCountry={handleHover}
          onHoverPosition={setHoverPosition}
          onSelectCountry={handleSelect}
          onHoverPin={setHoverPin}
          showLabels={showLabels}
          showCapitals={showCapitals}
          showAirTraffic={showAirTraffic}
          airTraffic={airTraffic}
          pins={pins}
        />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-black/40 via-black/10 to-black/50" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_25%_15%,rgba(255,255,255,0.08),transparent_55%)]" />
      </div>

      <div className="pointer-events-none relative z-10 flex min-h-screen flex-col">
        <header className="pointer-events-none flex items-start justify-between px-10 pt-8">
          <div className="pointer-events-auto flex items-center gap-3">
            <Image
              src="/mandala_logo.png"
              alt="Mandala"
              width={40}
              height={40}
              className="h-10 w-10 rounded-2xl object-contain"
              priority
            />
            <div className="flex flex-col gap-0.5">
              <p className="text-base font-semibold uppercase tracking-[0.38em] text-white/85">
                Mandala
              </p>
              <p className="text-sm font-[var(--font-display)] text-white/75">
                Geopolitics Desk
              </p>
            </div>
          </div>
          <div
            className="pointer-events-auto relative flex flex-col items-end gap-4"
            ref={refreshGroupRef}
          >
            <ControlBar
              showLabels={showLabels}
              showCapitals={showCapitals}
              showAirTraffic={showAirTraffic}
              isRefreshing={isRefreshing}
              showSignals={showSignals}
              showAgent={showAgent}
              onToggleLabels={() => setShowLabels((prev) => !prev)}
              onToggleCapitals={() => setShowCapitals((prev) => !prev)}
              onToggleAirTraffic={() => setShowAirTraffic((prev) => !prev)}
              onRefresh={handleRefresh}
              onToggleSignals={() => setShowSignals((prev) => !prev)}
              onToggleAgent={() => setShowAgent((prev) => !prev)}
            />

            {selectedCountry ? (
              <aside
                ref={focusPanelRef}
                className="pointer-events-auto flex w-[420px] max-h-[calc(100vh-200px)] flex-col overflow-hidden rounded-[32px] border border-white/10 bg-black/50 shadow-[0_24px_80px_rgba(10,10,10,0.35)] backdrop-blur"
              >
                <div className="flex min-h-0 flex-1 flex-col">
                  <div className="border-b border-white/10 px-6 py-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs uppercase tracking-[0.3em] text-white/60">
                          Country focus
                        </p>
                        <h1 className="text-2xl font-[var(--font-display)] text-white">
                          {selectedSnapshot?.name ?? selectedCountry}
                        </h1>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <button
                          type="button"
                          onClick={() => toggleFavorite(selectedCountry)}
                          className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 text-white/60 transition hover:bg-white/10"
                          aria-label={
                            favoriteCountries.includes(selectedCountry)
                              ? "Remove from favourites"
                              : "Add to favourites"
                          }
                          title={
                            favoriteCountries.includes(selectedCountry)
                              ? "Remove from favourites"
                              : "Add to favourites"
                          }
                        >
                          <svg
                            viewBox="0 0 24 24"
                            className="h-4 w-4"
                            fill={favoriteCountries.includes(selectedCountry) ? "currentColor" : "none"}
                            stroke="currentColor"
                            strokeWidth="1.6"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <path d="M12 17.3l-6.18 3.25 1.18-6.88L2 8.74l6.91-1 3.09-6.27 3.09 6.27 6.91 1-5 4.93 1.18 6.88z" />
                          </svg>
                        </button>
                        <span
                          className={`rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em] ${getStatusStyle(
                            selectedSnapshot?.activity_level,
                          )}`}
                        >
                          {selectedSnapshot?.activity_level ?? "Watching"}
                        </span>
                        {selectedSnapshot?.updated_at ? (
                          <span className="text-xs text-white/50">
                            {selectedSnapshot.updated_at}
                          </span>
                        ) : null}
                      </div>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-3 text-xs text-white/70">
                      <div className="rounded-2xl border border-white/10 bg-black/30 px-3 py-2">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-white/40">
                          Signals
                        </p>
                        <p className="text-lg text-white">
                          {selectedSnapshot?.stats?.signals ?? 0}
                        </p>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-black/30 px-3 py-2">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-white/40">
                          Disputes
                        </p>
                        <p className="text-lg text-white">
                          {selectedSnapshot?.stats?.disputes ?? 0}
                        </p>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-black/30 px-3 py-2">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-white/40">
                          Confidence
                        </p>
                        <p className="text-lg text-white">
                          {selectedSnapshot?.stats?.confidence ?? 0}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto px-6 py-6">
                    <div className="mb-4 flex items-center justify-between text-xs uppercase tracking-[0.3em] text-white/60">
                      Event clusters
                      <span className="rounded-full bg-white/10 px-3 py-1 text-[10px] text-white/70">
                        {selectedEvents.length} active
                      </span>
                    </div>

                    <div className="flex flex-col gap-4">
                      {selectedEvents.map((event) => (
                        <div
                          key={event.title}
                          className="rounded-3xl border border-white/10 bg-black/30 p-4"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <h2 className="text-base font-semibold text-white">{event.title}</h2>
                              {event.summary ? (
                                <p className="mt-2 text-sm text-white/70">
                                  {truncateText(event.summary, 180)}
                                </p>
                              ) : null}
                            </div>
                            <span className="rounded-full bg-white/10 px-3 py-1 text-[10px] uppercase tracking-[0.2em] text-white/70">
                              {event.confidence}
                            </span>
                          </div>
                          {event.sources.length > 0 || event.updated_at ? (
                            <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px] text-white/60">
                              {event.sources.map((source) => (
                                <a
                                  key={`${source.name}-${source.url}`}
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="rounded-full border border-white/10 bg-black/40 px-3 py-1 transition hover:bg-black/20"
                                >
                                  {source.name}
                                </a>
                              ))}
                              {event.updated_at ? (
                                <span className="ml-auto text-[10px] uppercase tracking-[0.2em] text-white/40">
                                  {event.updated_at}
                                </span>
                              ) : null}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </aside>
            ) : null}
            {showAgent ? (
              <ChatPanel
                onClose={() => setShowAgent(false)}
                onSend={handleAgentSend}
                onClear={() => setAgentMessages([])}
                messages={agentMessages}
                isSending={isAgentSending}
              />
            ) : null}
          </div>
        </header>

        <div className="flex-1">
          <div className="absolute left-0 right-0 top-0 bottom-16">
          {showSignals ? (
            <SignalsFeed
              feedTab={feedTab}
              onChangeTab={setFeedTab}
              feedQuery={feedQuery}
              onChangeQuery={setFeedQuery}
              lastUpdated={lastSignalsUpdate}
              showFilters={showFeedFilters}
              onShowFilters={setShowFeedFilters}
              feedCountry={feedCountry}
              onChangeCountry={setFeedCountry}
              feedOutlet={feedOutlet}
              onChangeOutlet={setFeedOutlet}
              feedTopic={feedTopic}
              onChangeTopic={setFeedTopic}
              feedRangeDays={feedRangeDays}
              onChangeRangeDays={setFeedRangeDays}
              countriesList={countriesList}
              outletsList={outletsList}
              topicsList={topicsList}
              feedItems={feedItems}
              notams={notams}
              getStatusStyle={getStatusStyle}
              truncateText={truncateText}
              onClose={() => setShowSignals(false)}
            />
          ) : null}
          </div>

          <MarketsFeed items={marketItems} />

          {hoverPosition && (hoverPin || (hoveredCountry && hoverCopy)) ? (
            <div
              className="pointer-events-none absolute z-20 flex w-72 flex-col gap-2 rounded-3xl border border-black/10 bg-white/85 p-4 shadow-[0_16px_40px_rgba(30,32,27,0.18)] backdrop-blur"
              style={{
                left:
                  hoverPosition.x + 18 + 288 > viewport.width
                    ? hoverPosition.x - 288 - 18
                    : hoverPosition.x + 18,
                top:
                  hoverPosition.y + 18 + 140 > viewport.height
                    ? hoverPosition.y - 140 - 18
                    : hoverPosition.y + 18,
              }}
            >
              <p className="text-[10px] uppercase tracking-[0.2em] text-black/50">Preview</p>
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-base font-[var(--font-display)] text-black">
                  {hoverPin ? hoverPin.title : hoverSnapshot?.name ?? hoveredCountry}
                </h3>
                {hoverPin ? (
                  <span className="rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-black/60">
                    {hoverPin.source}
                  </span>
                ) : (
                  <span
                    className={`rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.2em] ${getStatusStyle(
                      hoveredStatus,
                    )}`}
                  >
                    {hoveredStatus}
                  </span>
                )}
              </div>
              {hoverPin?.summary || hoverCopy?.text ? (
                <p className="text-xs text-black/80">
                  {hoverPin
                    ? truncateText(hoverPin.summary, 160)
                    : hoverCopy?.text}
                </p>
              ) : null}
              {hoverPin?.updatedAt || hoverCopy?.timestamp ? (
                <p className="text-[10px] text-black/50">
                  {hoverPin ? hoverPin.updatedAt : hoverCopy?.timestamp}
                </p>
              ) : null}
            </div>
          ) : null}

        </div>

      </div>
    </div>
  );
}
