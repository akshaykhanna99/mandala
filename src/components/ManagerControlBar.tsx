"use client";

import { useState } from "react";
import SettingsModal from "./SettingsModal";

export default function ManagerControlBar() {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <>
      <div className="flex items-center gap-2 rounded-full border border-white/20 bg-black/40 px-3 py-2 backdrop-blur">
        <button
          type="button"
          onClick={() => setShowSettings(true)}
          className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80 transition hover:bg-white/10"
          aria-label="Settings"
          title="Settings"
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
          <circle cx="12" cy="12" r="3" />
          <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24" />
        </svg>
      </button>
    </div>
    
    <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </>
  );
}
