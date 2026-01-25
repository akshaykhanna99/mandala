"""Database operations for snapshots, global items, and market items."""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import CountrySnapshot, GlobalItem, MarketItem
from .database import engine, SessionLocal, Base
from .db_models import (
    CountrySnapshotTable,
    GlobalItemTable,
    MarketItemTable,
)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def _snapshot_to_pydantic(db_snapshot: CountrySnapshotTable) -> CountrySnapshot:
    """Convert database model to Pydantic model."""
    return CountrySnapshot(
        id=db_snapshot.id,
        name=db_snapshot.name,
        activity_level=db_snapshot.activity_level,
        updated_at=db_snapshot.updated_at,
        events=db_snapshot.events,
        stats=db_snapshot.stats,
    )


def _global_item_to_pydantic(db_item: GlobalItemTable) -> GlobalItem:
    """Convert database model to Pydantic model."""
    return GlobalItem(
        title=db_item.title,
        summary=db_item.summary,
        source=db_item.source,
        url=db_item.url,
        published_at=db_item.published_at,
        topic=db_item.topic,
        countries=db_item.countries or [],
        country_ids=db_item.country_ids or [],
    )


def _market_item_to_pydantic(db_item: MarketItemTable) -> MarketItem:
    """Convert database model to Pydantic model."""
    return MarketItem(
        id=db_item.id,
        name=db_item.name,
        symbol=db_item.symbol,
        category=db_item.category,
        price=db_item.price,
        change=db_item.change,
        change_pct=db_item.change_pct,
        updated_at=db_item.updated_at,
        source=db_item.source,
    )


def load_snapshots() -> List[CountrySnapshot]:
    """Load all country snapshots from database."""
    db = SessionLocal()
    try:
        db_snapshots = db.query(CountrySnapshotTable).all()
        return [_snapshot_to_pydantic(s) for s in db_snapshots]
    finally:
        db.close()


def save_snapshots(snapshots: List[CountrySnapshot]) -> None:
    """Save country snapshots to database (replaces all)."""
    db = SessionLocal()
    try:
        # Delete all existing snapshots
        db.query(CountrySnapshotTable).delete()
        
        # Insert new snapshots
        for snapshot in snapshots:
            db_snapshot = CountrySnapshotTable(
                id=snapshot.id or snapshot.name.lower().replace(" ", "-"),
                name=snapshot.name,
                activity_level=snapshot.activity_level,
                updated_at=snapshot.updated_at,
                events=[event.model_dump() for event in snapshot.events],
                stats=snapshot.stats.model_dump(),
            )
            db.add(db_snapshot)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def load_global_items() -> List[GlobalItem]:
    """Load all global items from database."""
    db = SessionLocal()
    try:
        db_items = db.query(GlobalItemTable).all()
        return [_global_item_to_pydantic(item) for item in db_items]
    finally:
        db.close()


def save_global_items(items: List[GlobalItem]) -> None:
    """Save global items to database (replaces all)."""
    db = SessionLocal()
    try:
        # Delete all existing global items
        db.query(GlobalItemTable).delete()
        
        # Insert new items
        for item in items:
            db_item = GlobalItemTable(
                title=item.title,
                summary=item.summary,
                source=item.source.model_dump(),
                url=item.url,
                published_at=item.published_at,
                topic=item.topic,
                countries=item.countries or [],
                country_ids=item.country_ids or [],
            )
            db.add(db_item)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def load_market_items() -> List[MarketItem]:
    """Load all market items from database."""
    db = SessionLocal()
    try:
        db_items = db.query(MarketItemTable).all()
        return [_market_item_to_pydantic(item) for item in db_items]
    finally:
        db.close()


def save_market_items(items: List[MarketItem]) -> None:
    """Save market items to database (replaces all)."""
    db = SessionLocal()
    try:
        # Delete all existing market items
        db.query(MarketItemTable).delete()
        
        # Insert new items
        for item in items:
            db_item = MarketItemTable(
                id=item.id,
                name=item.name,
                symbol=item.symbol,
                category=item.category,
                price=item.price,
                change=item.change,
                change_pct=item.change_pct,
                updated_at=item.updated_at,
                source=item.source,
            )
            db.add(db_item)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
