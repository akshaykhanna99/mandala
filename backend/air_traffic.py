import os
from datetime import datetime, timezone
from typing import List, Dict

import httpx


OPENSKY_URL = "https://opensky-network.org/api/states/all"


def _now_label() -> str:
    return datetime.now(timezone.utc).strftime("Updated %Y-%m-%d %H:%M UTC")


def fetch_air_traffic() -> List[Dict]:
    auth_user = os.getenv("OPENSKY_USERNAME", "").strip()
    auth_pass = os.getenv("OPENSKY_PASSWORD", "").strip()
    auth = (auth_user, auth_pass) if auth_user and auth_pass else None

    response = httpx.get(OPENSKY_URL, auth=auth, timeout=20)
    response.raise_for_status()
    data = response.json()
    states = data.get("states") or []
    updated_at = _now_label()
    results = []
    for state in states:
        if len(state) < 8:
            continue
        icao24 = state[0]
        callsign = (state[1] or "").strip()
        origin_country = state[2] or ""
        longitude = state[5]
        latitude = state[6]
        velocity = state[9] if len(state) > 9 else None
        if longitude is None or latitude is None:
            continue
        results.append(
            {
                "id": icao24,
                "callsign": callsign,
                "origin_country": origin_country,
                "longitude": longitude,
                "latitude": latitude,
                "velocity": velocity,
                "updated_at": updated_at,
            }
        )
    return results
