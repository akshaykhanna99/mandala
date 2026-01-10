import os
from typing import List

import httpx

from .data_store import load_global_items, load_market_items, load_snapshots
from .models import AgentRequest, AgentResponse, GlobalItem, MarketItem, CountrySnapshot


def _build_context(
    global_items: List[GlobalItem],
    snapshots: List[CountrySnapshot],
    markets: List[MarketItem],
) -> str:
    lines: List[str] = []
    lines.append("Context summary (latest signals and markets):")

    if global_items:
        lines.append("Signals feed highlights:")
        for item in global_items[:20]:
            countries = ", ".join(item.countries) if item.countries else "Unknown"
            lines.append(
                f"- {item.title} ({countries}) | {item.source.name} | {item.published_at}"
            )
            if item.summary:
                lines.append(f"  Summary: {item.summary}")

    if snapshots:
        lines.append("Country event clusters:")
        for snapshot in snapshots[:10]:
            if not snapshot.events:
                continue
            lines.append(f"- {snapshot.name} ({snapshot.activity_level})")
            for event in snapshot.events[:2]:
                lines.append(f"  • {event.title} | {event.updated_at}")

    if markets:
        lines.append("Markets snapshot:")
        for market in markets[:12]:
            change = f"{market.change_pct:.2f}%" if market.change_pct is not None else "n/a"
            lines.append(
                f"- {market.name} ({market.symbol}) {market.price} ({change})"
            )

    return "\n".join(lines)


def query_agent(payload: AgentRequest) -> AgentResponse:
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

    global_items = load_global_items()
    snapshots = load_snapshots()
    markets = load_market_items()

    context = _build_context(global_items, snapshots, markets)
    system_prompt = (
        "You are Chanakya, a geopolitics intelligence assistant. "
        "Answer clearly and concisely in 5-7 sentences max. "
        "If you use context, cite sources by name. "
        "If the context is insufficient, say so and ask a follow-up."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{payload.query}\n\n{context}"},
    ]

    response = httpx.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": 280},
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    content = data.get("message", {}).get("content", "").strip()
    return AgentResponse(answer=content or "No response generated.")
