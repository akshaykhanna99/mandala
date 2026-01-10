import os
from datetime import datetime, timezone
from typing import Dict, List, Any

import httpx


DEFAULT_NOTAM_URL = "https://api.aviationapi.com/v1/notams"


def _now_label() -> str:
    return datetime.now(timezone.utc).strftime("Updated %Y-%m-%d %H:%M UTC")


def _coerce_item(raw: Dict[str, Any]) -> Dict[str, str]:
    return {
        "id": str(raw.get("NOTAMNumber") or raw.get("id") or raw.get("notam_id") or ""),
        "location": str(raw.get("ICAO") or raw.get("location") or raw.get("airport") or ""),
        "issued_at": str(raw.get("issued") or raw.get("issue_date") or raw.get("time") or ""),
        "summary": str(raw.get("text") or raw.get("summary") or raw.get("raw") or ""),
        "source": "NOTAM",
        "updated_at": _now_label(),
    }


def fetch_notams() -> List[Dict[str, str]]:
    base_url = os.getenv("NOTAM_API_BASE", DEFAULT_NOTAM_URL).strip()
    airports = os.getenv("NOTAM_AIRPORTS", "").strip()
    params = {"apt": airports} if airports else None
    try:
        response = httpx.get(base_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        print(f"[notams] request failed: {exc}")
        return []

    items: List[Dict[str, str]] = []
    if isinstance(data, list):
        for raw in data:
            if isinstance(raw, dict):
                items.append(_coerce_item(raw))
        return items

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                for raw in value:
                    if isinstance(raw, dict):
                        items.append(_coerce_item(raw))
        return items

    return items
