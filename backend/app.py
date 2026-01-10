from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .air_traffic import fetch_air_traffic
from .agent import query_agent
from .notams import fetch_notams
from .data_store import (
    load_global_items,
    load_market_items,
    load_snapshots,
    save_global_items,
    save_market_items,
    save_snapshots,
)
from .markets import fetch_market_items
from .sources import build_global_items, build_snapshots
from .models import AgentRequest

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/countries")
def list_countries():
    return [snapshot.model_dump() for snapshot in load_snapshots()]


@app.get("/global")
def list_global():
    return [item.model_dump() for item in load_global_items()]


@app.get("/markets")
def list_markets():
    return [item.model_dump() for item in load_market_items()]


@app.get("/air-traffic")
def list_air_traffic():
    return fetch_air_traffic()

@app.get("/notams")
def list_notams():
    return fetch_notams()


@app.post("/agent/query")
def agent_query(payload: AgentRequest):
    return query_agent(payload).model_dump()


@app.get("/countries/{country_name}")
def get_country(country_name: str):
    snapshots = load_snapshots()
    for snapshot in snapshots:
        if snapshot.name.lower() == country_name.lower() or snapshot.id.lower() == country_name.lower():
            return snapshot.model_dump()
    raise HTTPException(status_code=404, detail="Country not found")


@app.post("/refresh")
def refresh_data(days: int = Query(1, ge=1, le=7)):
    try:
        global_items = build_global_items(max_age_days=days)
        snapshots = build_snapshots(global_items)
        market_items = fetch_market_items()
        save_snapshots(snapshots)
        save_global_items(global_items)
        save_market_items(market_items)
        return {
            "status": "ok",
            "countries": len(snapshots),
            "global_items": len(global_items),
            "market_items": len(market_items),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
