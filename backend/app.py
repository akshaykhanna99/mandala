from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import array

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
    init_db,
)
from .markets import fetch_market_items
from .sources import build_global_items, build_snapshots
from .models import AgentRequest
from .routes import geo_risk, themes, scoring_settings, asset_search, gp_scans, reports

load_dotenv()

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    init_db()
    
    # Auto-seed themes if table is empty
    try:
        from .database import SessionLocal
        from .db_models import ThemeTable
        from .routes.themes import _seed_default_themes
        db = SessionLocal()
        try:
            theme_count = db.query(ThemeTable).count()
            if theme_count == 0:
                result = _seed_default_themes(db)
                print(f"✅ Auto-seeded themes: {result['message']}")
        except Exception as e:
            print(f"⚠️  Could not auto-seed themes: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️  Error during theme auto-seeding: {e}")

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
    try:
        return fetch_air_traffic()
    except Exception as exc:
        # Log the error and return empty array instead of crashing
        print(f"Error fetching air traffic: {exc}")
        return []

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
    """
    Refresh data from live RSS feeds and save to database.
    
    This fetches live data from:
    - BBC World, Al Jazeera, DW World, UN News, ReliefWeb, NATO, IAEA
    
    Args:
        days: How many days back to fetch (1-7)
    
    Returns:
        Status and counts of items fetched
    """
    try:
        global_items = build_global_items(max_age_days=days)
        snapshots = build_snapshots(global_items)
        market_items = fetch_market_items()
        save_snapshots(snapshots)
        save_global_items(global_items)
        save_market_items(market_items)
        
        # Invalidate intelligence cache when new data is loaded
        from .geo_risk_intelligence_cache import invalidate_cache
        invalidate_cache()
        
        return {
            "status": "ok",
            "countries": len(snapshots),
            "global_items": len(global_items),
            "market_items": len(market_items),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/db-stats")
def get_db_stats():
    """
    Get statistics about what's in the database.
    
    Useful for debugging - shows counts and sample data.
    """
    from .database import SessionLocal
    from .db_models import GlobalItemTable, CountrySnapshotTable
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Count total items
        total_global_items = db.query(GlobalItemTable).count()
        total_snapshots = db.query(CountrySnapshotTable).count()
        
        # Count recent items (last 90 days)
        cutoff_date = datetime.now() - timedelta(days=90)
        recent_global_items = db.query(GlobalItemTable).filter(
            GlobalItemTable.created_at >= cutoff_date
        ).count()
        
        recent_snapshots = db.query(CountrySnapshotTable).filter(
            CountrySnapshotTable.updated_at_db >= cutoff_date
        ).count()
        
        # Get sample countries
        sample_snapshots = db.query(CountrySnapshotTable).limit(10).all()
        countries = [{"name": s.name, "activity_level": s.activity_level} for s in sample_snapshots]
        
        # Get sample global items with countries
        sample_items = db.query(GlobalItemTable).limit(10).all()
        items = [
            {
                "title": item.title[:100],
                "countries": item.countries,
                "topic": item.topic,
                "published_at": item.published_at,
            }
            for item in sample_items
        ]
        
        # Check for Turkey specifically
        turkey_items = db.query(GlobalItemTable).filter(
            GlobalItemTable.countries.op('&&')(array(['Turkey']))
        ).count()
        
        turkey_snapshots = db.query(CountrySnapshotTable).filter(
            CountrySnapshotTable.name.ilike('%Turkey%')
        ).count()
        
        return {
            "total_global_items": total_global_items,
            "total_snapshots": total_snapshots,
            "recent_global_items_90d": recent_global_items,
            "recent_snapshots_90d": recent_snapshots,
            "turkey_items": turkey_items,
            "turkey_snapshots": turkey_snapshots,
            "sample_countries": countries,
            "sample_items": items,
        }
    finally:
        db.close()


# Include routes
app.include_router(geo_risk.router)
app.include_router(themes.router)
app.include_router(scoring_settings.router)
app.include_router(asset_search.router)
app.include_router(gp_scans.router)
app.include_router(reports.router)
