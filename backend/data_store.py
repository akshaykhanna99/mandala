import json
from pathlib import Path
from typing import List

from .models import CountrySnapshot, GlobalItem, MarketItem

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "snapshots.json"
GLOBAL_FILE = DATA_DIR / "global.json"
MARKETS_FILE = DATA_DIR / "markets.json"


def load_snapshots() -> List[CountrySnapshot]:
    if not DATA_FILE.exists():
        return []
    raw = json.loads(DATA_FILE.read_text())
    return [CountrySnapshot(**item) for item in raw]


def save_snapshots(snapshots: List[CountrySnapshot]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [snapshot.model_dump() for snapshot in snapshots]
    DATA_FILE.write_text(json.dumps(payload, indent=2))


def load_global_items() -> List[GlobalItem]:
    if not GLOBAL_FILE.exists():
        return []
    raw = json.loads(GLOBAL_FILE.read_text())
    return [GlobalItem(**item) for item in raw]


def save_global_items(items: List[GlobalItem]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump() for item in items]
    GLOBAL_FILE.write_text(json.dumps(payload, indent=2))


def load_market_items() -> List[MarketItem]:
    if not MARKETS_FILE.exists():
        return []
    raw = json.loads(MARKETS_FILE.read_text())
    return [MarketItem(**item) for item in raw]


def save_market_items(items: List[MarketItem]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump() for item in items]
    MARKETS_FILE.write_text(json.dumps(payload, indent=2))
