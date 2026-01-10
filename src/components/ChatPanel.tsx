"use client";

import { useEffect, useRef, useState } from "react";

type ChatPanelProps = {
  onClose: () => void;
  onSend: (message: string) => void;
  onClear: () => void;
  messages: { role: "user" | "assistant"; content: string }[];
  isSending: boolean;
};

export default function ChatPanel({
  onClose,
  onSend,
  onClear,
  messages,
  isSending,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement | null>(null);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) {
      return;
    }
    onSend(trimmed);
    setInput("");
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, isSending]);

  return (
    <aside className="pointer-events-auto h-[calc(100vh-200px)] w-[360px] overflow-hidden rounded-[28px] border border-white/10 bg-black/40 shadow-[0_24px_80px_rgba(10,10,10,0.35)] backdrop-blur">
      <div className="flex h-full min-h-0 flex-col">
        <div className="border-b border-white/10 px-5 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">Chanakya</p>
              <p className="mt-2 text-sm text-white/60">Strategic reasoning agent.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClear}
                className="rounded-full border border-white/15 px-3 py-1 text-[10px] uppercase tracking-[0.2em] text-white/60 transition hover:text-white"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-white/15 text-white/70 transition hover:text-white"
                aria-label="Close agent panel"
                title="Close agent panel"
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
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          {messages.length === 0 ? (
            <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-white/60">
              No messages yet.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`rounded-2xl border px-4 py-3 text-sm ${
                    message.role === "user"
                      ? "border-white/10 bg-white/10 text-white"
                      : "border-white/10 bg-black/30 text-white/70"
                  }`}
                >
                  <p className="text-[10px] uppercase tracking-[0.2em] text-white/40">
                    {message.role === "user" ? "You" : "Chanakya"}
                  </p>
                  <p className="mt-2 whitespace-pre-wrap">{message.content}</p>
                </div>
              ))}
            </div>
          )}
          <div ref={endRef} />
        </div>
        <form className="border-t border-white/10 px-4 py-3" onSubmit={handleSubmit}>
          <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-black/30 px-3 py-2">
            <input
              type="text"
              placeholder="Ask Chanakya..."
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="flex-1 bg-transparent text-sm text-white/80 placeholder:text-white/40 focus:outline-none"
            />
            <button
              type="submit"
              disabled={isSending}
              className="rounded-full border border-white/20 px-3 py-1 text-[10px] uppercase tracking-[0.2em] text-white/70 disabled:text-white/40"
            >
              {isSending ? "Sending" : "Send"}
            </button>
          </div>
        </form>
      </div>
    </aside>
  );
}
