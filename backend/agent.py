import os
import re
from typing import List, Set

import httpx

from .data_store import load_global_items, load_market_items, load_snapshots
from .models import AgentRequest, AgentResponse, GlobalItem, MarketItem, CountrySnapshot


def _tokenize(text: str) -> Set[str]:
    return set(re.findall(r"[a-zA-Z]{3,}", text.lower()))


def _clean_text(text: str, limit: int = 240) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > limit:
        cleaned = f"{cleaned[:limit].rstrip()}..."
    return cleaned


def _is_relevant(text: str, query_terms: Set[str]) -> bool:
    if not query_terms:
        return True
    return bool(_tokenize(text) & query_terms)


def _build_context(
    query_terms: Set[str],
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
                lines.append(f"  Summary: {_clean_text(item.summary)}")

    if snapshots:
        lines.append("Country event clusters:")
        for snapshot in snapshots[:10]:
            if not snapshot.events:
                continue
            lines.append(f"- {snapshot.name} ({snapshot.activity_level})")
            added = 0
            for event in snapshot.events:
                if added >= 2:
                    break
                haystack = " ".join(
                    [event.title, event.summary, event.why, event.topic, snapshot.name]
                )
                if _is_relevant(haystack, query_terms):
                    lines.append(f"  • {event.title} | {event.updated_at}")
                    added += 1

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

    query_terms = _tokenize(payload.query)

    filtered_globals = [
        item
        for item in global_items
        if _is_relevant(
            " ".join(
                [
                    item.title,
                    item.summary,
                    item.topic,
                    item.source.name,
                    " ".join(item.countries or []),
                ]
            ),
            query_terms,
        )
    ]
    filtered_snapshots = []
    for snapshot in snapshots:
        if _is_relevant(snapshot.name, query_terms):
            filtered_snapshots.append(snapshot)
            continue
        for event in snapshot.events:
            haystack = " ".join([event.title, event.summary, event.why, event.topic])
            if _is_relevant(haystack, query_terms):
                filtered_snapshots.append(snapshot)
                break

    filtered_markets = [
        market
        for market in markets
        if _is_relevant(
            " ".join([market.name, market.symbol, market.category, market.source]),
            query_terms,
        )
    ]

    context = _build_context(
        query_terms,
        filtered_globals or [],
        filtered_snapshots or [],
        filtered_markets or [],
    )
    if not filtered_globals and not filtered_snapshots and not filtered_markets:
        context = f"{context}\nNo relevant items found in local feeds."
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
