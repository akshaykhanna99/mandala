from pydantic import BaseModel
from typing import List


class SourceRef(BaseModel):
    name: str
    url: str


class EventCluster(BaseModel):
    title: str
    summary: str
    why: str
    confidence: str
    sources: List[SourceRef]
    updated_at: str
    topic: str


class CountryStats(BaseModel):
    signals: int
    disputes: int
    confidence: float


class CountrySnapshot(BaseModel):
    id: str = ""
    name: str
    activity_level: str
    updated_at: str
    events: List[EventCluster]
    stats: CountryStats


class GlobalItem(BaseModel):
    title: str
    summary: str
    source: SourceRef
    url: str
    published_at: str
    topic: str
    countries: List[str]
    country_ids: List[str] = []


class MarketItem(BaseModel):
    id: str
    name: str
    symbol: str
    category: str
    price: float
    change: float | None = None
    change_pct: float | None = None
    updated_at: str
    source: str


class AgentRequest(BaseModel):
    query: str


class AgentResponse(BaseModel):
    answer: str
