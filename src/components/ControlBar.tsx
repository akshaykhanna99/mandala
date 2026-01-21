"use client";

type ControlBarProps = {
  showLabels: boolean;
  showCapitals: boolean;
  showAirTraffic: boolean;
  useGlobe: boolean;
  isRefreshing: boolean;
  showSignals: boolean;
  showAgent: boolean;
  onToggleLabels: () => void;
  onToggleCapitals: () => void;
  onToggleAirTraffic: () => void;
  onToggleGlobe: () => void;
  onRefresh: () => void;
  onToggleSignals: () => void;
  onToggleAgent: () => void;
};

export default function ControlBar({
  showLabels,
  showCapitals,
  showAirTraffic,
  useGlobe,
  isRefreshing,
  showSignals,
  showAgent,
  onToggleLabels,
  onToggleCapitals,
  onToggleAirTraffic,
  onToggleGlobe,
  onRefresh,
  onToggleSignals,
  onToggleAgent,
}: ControlBarProps) {
  return (
    <div className="flex items-center gap-2 rounded-full border border-white/20 bg-black/40 px-3 py-2">
      <button
        type="button"
        onClick={onToggleSignals}
        className={`flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80 transition hover:bg-white/10 ${
          showSignals ? "bg-white/10" : ""
        }`}
        aria-label={showSignals ? "Hide signals feed" : "Show signals feed"}
        title={showSignals ? "Hide signals feed" : "Show signals feed"}
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
          <circle cx="12" cy="12" r="9" />
          <path d="M3 12h18" />
          <path d="M12 3a12 12 0 0 1 0 18" />
          <path d="M12 3a12 12 0 0 0 0 18" />
        </svg>
      </button>
      <button
        type="button"
        onClick={onToggleGlobe}
        className={`flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80 transition hover:bg-white/10 ${
          useGlobe ? "bg-white/10" : ""
        }`}
        aria-label={useGlobe ? "Switch to flat map" : "Switch to globe view"}
        title={useGlobe ? "Switch to flat map" : "Switch to globe view"}
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
          <path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z" />
          <path d="M9 4v14" />
          <path d="M15 6v14" />
        </svg>
      </button>
      <button
        type="button"
        onClick={onToggleAgent}
        className={`flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80 transition hover:bg-white/10 ${
          showAgent ? "bg-white/10" : ""
        }`}
        aria-label={showAgent ? "Hide agent panel" : "Show agent panel"}
        title={showAgent ? "Hide agent panel" : "Show agent panel"}
      >
        <img
          src="/chanakya_logo.svg"
          alt="Chanakya"
          className="h-6 w-6 invert scale-125"
        />
      </button>
      <button
        type="button"
        onClick={onToggleLabels}
        className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80 transition hover:bg-white/10"
        aria-label={showLabels ? "Hide labels" : "Show labels"}
        title={showLabels ? "Hide labels" : "Show labels"}
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
          <rect x="3" y="4" width="18" height="12" rx="2" />
          <path d="M7 8h10" />
          <path d="M7 12h6" />
          <path d="M8 20l2-4h4l2 4" />
        </svg>
      </button>
      <button
        type="button"
        onClick={onToggleCapitals}
        className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80 transition hover:bg-white/10"
        aria-label={showCapitals ? "Hide capitals" : "Show capitals"}
        title={showCapitals ? "Hide capitals" : "Show capitals"}
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
          <circle cx="12" cy="8" r="3" />
          <path d="M12 11v8" />
          <path d="M9 19h6" />
        </svg>
      </button>
      <button
        type="button"
        onClick={onToggleAirTraffic}
        className={`flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80 transition hover:bg-white/10 ${
          showAirTraffic ? "bg-white/10" : ""
        }`}
        aria-label={showAirTraffic ? "Hide air traffic" : "Show air traffic"}
        title={showAirTraffic ? "Hide air traffic" : "Show air traffic"}
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
          <path d="M21 16l-8.5-3V7.5l2.5-1V4l-3 1-3-1v2.5l2.5 1V13L3 16v2l8.5-2.5V20l-2.5 1.5V23l3-1 3 1v-1.5L12.5 20v-4.5L21 18v-2z" />
        </svg>
      </button>
      <button
        type="button"
        onClick={onRefresh}
        className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80 transition hover:bg-white/10"
        aria-label="Refresh feed"
        title="Refresh feed"
      >
        <svg
          viewBox="0 0 24 24"
          className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 12a9 9 0 1 1-3.3-6.9" />
          <path d="M21 3v6h-6" />
        </svg>
      </button>
    </div>
  );
}
