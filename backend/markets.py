import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import httpx

from .models import MarketItem

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
STOOQ_BASE_URL = "https://stooq.com/q/d/l/"
COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
)


@dataclass(frozen=True)
class StooqSymbol:
    symbol: str
    name: str
    category: str


@dataclass(frozen=True)
class FredSeries:
    series_id: str
    name: str
    category: str


STOOQ_SYMBOLS = [
    StooqSymbol("spy.us", "S&P 500 (SPY)", "Equities"),
    StooqSymbol("gld.us", "Gold (GLD)", "Metals"),
    StooqSymbol("slv.us", "Silver (SLV)", "Metals"),
    StooqSymbol("pplt.us", "Platinum (PPLT)", "Metals"),
    StooqSymbol("pall.us", "Palladium (PALL)", "Metals"),
    StooqSymbol("aapl.us", "Apple", "Stocks"),
    StooqSymbol("msft.us", "Microsoft", "Stocks"),
    StooqSymbol("nvda.us", "Nvidia", "Stocks"),
    StooqSymbol("tsla.us", "Tesla", "Stocks"),
]

FRED_SERIES = [
    FredSeries("DGS2", "US 2Y Yield", "Rates"),
    FredSeries("DGS10", "US 10Y Yield", "Rates"),
    FredSeries("DGS30", "US 30Y Yield", "Rates"),
    FredSeries("T10Y2Y", "10Y-2Y Spread", "Rates"),
]


def _now_label() -> str:
    return datetime.now(timezone.utc).strftime("Updated %Y-%m-%d %H:%M UTC")


def _fetch_stooq_series(symbol: str) -> List[float]:
    url = STOOQ_BASE_URL
    params = {"s": symbol, "i": "d"}
    response = httpx.get(url, params=params, timeout=20)
    response.raise_for_status()
    lines = response.text.strip().splitlines()
    if len(lines) < 2:
        return []
    values = []
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 5:
            continue
        try:
            close = float(parts[4])
        except ValueError:
            continue
        values.append(close)
    return values


def _fetch_fred_series(series_id: str, api_key: str) -> List[float]:
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 10,
    }
    response = httpx.get(FRED_BASE_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    observations = data.get("observations", [])
    values = []
    for obs in observations:
        raw = obs.get("value")
        if raw is None or raw == ".":
            continue
        try:
            values.append(float(raw))
        except ValueError:
            continue
        if len(values) >= 2:
            break
    return values


def _build_change(values: List[float]) -> tuple[float | None, float | None]:
    if len(values) < 2:
        return None, None
    latest, previous = values[0], values[1]
    change = latest - previous
    change_pct = (change / previous) * 100 if previous != 0 else None
    return change, change_pct


def fetch_market_items() -> List[MarketItem]:
    items: List[MarketItem] = []
    updated_at = _now_label()

    for symbol in STOOQ_SYMBOLS:
        try:
            values = _fetch_stooq_series(symbol.symbol)
        except Exception:
            continue
        if not values:
            continue
        change, change_pct = _build_change(values)
        items.append(
            MarketItem(
                id=symbol.symbol,
                name=symbol.name,
                symbol=symbol.symbol.upper(),
                category=symbol.category,
                price=values[0],
                change=change,
                change_pct=change_pct,
                updated_at=updated_at,
                source="Stooq",
            )
        )

    fred_key = os.getenv("FRED_API_KEY", "").strip()
    if fred_key:
        for series in FRED_SERIES:
            try:
                values = _fetch_fred_series(series.series_id, fred_key)
            except Exception:
                continue
            if not values:
                continue
            change, change_pct = _build_change(values)
            items.append(
                MarketItem(
                    id=series.series_id,
                    name=series.name,
                    symbol=series.series_id,
                    category=series.category,
                    price=values[0],
                    change=change,
                    change_pct=change_pct,
                    updated_at=updated_at,
                    source="FRED",
                )
            )

    try:
        response = httpx.get(COINGECKO_URL, timeout=20)
        response.raise_for_status()
        data = response.json().get("bitcoin", {})
        price = data.get("usd")
        change_pct = data.get("usd_24h_change")
        if price is not None:
            items.append(
                MarketItem(
                    id="bitcoin",
                    name="Bitcoin",
                    symbol="BTC",
                    category="Crypto",
                    price=float(price),
                    change=None,
                    change_pct=float(change_pct) if change_pct is not None else None,
                    updated_at=updated_at,
                    source="CoinGecko",
                )
            )
    except Exception:
        pass

    return items
