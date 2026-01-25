"""Filtered database queries for intelligence retrieval.

This module provides optimized database queries that filter at the database level
instead of loading all data into memory. This significantly improves performance
for intelligence retrieval operations.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, case
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.exc import OperationalError
import time

from .models import CountrySnapshot, GlobalItem
from .database import SessionLocal
from .db_models import CountrySnapshotTable, GlobalItemTable
from .data_store import _snapshot_to_pydantic, _global_item_to_pydantic


def _retry_db_query(func, max_retries=3, delay=1):
    """Retry a database query with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except OperationalError as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"Database connection error (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Database query failed after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            # Don't retry on non-connection errors
            raise


def load_global_items_filtered(
    countries: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    days_lookback: int = 90,
    limit: int = 100,
    min_relevance: float = 0.0,
) -> List[GlobalItem]:
    """
    Load global items with database-level filtering.
    
    This is much more efficient than loading all items and filtering in Python.
    
    Args:
        countries: Filter by countries (array containment)
        topics: Filter by topics
        days_lookback: Only include items from last N days
        limit: Maximum number of items to return
        min_relevance: Minimum relevance (not used in DB query, for post-filtering)
    
    Returns:
        List of filtered GlobalItem objects
    """
    def _execute_query():
        db = SessionLocal()
        try:
            query = db.query(GlobalItemTable)
            
            # Filter by countries (array containment)
            if countries:
                # PostgreSQL array containment: WHERE countries @> ARRAY['Turkey']
                conditions = []
                for country in countries:
                    # Use array overlap operator: countries && ARRAY[country]
                    conditions.append(GlobalItemTable.countries.op('&&')(array([country])))
                if conditions:
                    query = query.filter(or_(*conditions))
            
            # Filter by topics
            if topics:
                query = query.filter(GlobalItemTable.topic.in_(topics))
            
            # Filter by date (published_at is a string, so we need to parse)
            # For now, we'll do date filtering in Python after loading
            # TODO: Add a computed column or proper date column for better performance
            
            # Order by created_at (newest first) and limit
            query = query.order_by(GlobalItemTable.created_at.desc()).limit(limit)
            
            db_items = query.all()
            items = [_global_item_to_pydantic(item) for item in db_items]
            
            # Filter by date in Python (since published_at is a string)
            if days_lookback > 0:
                cutoff_date = datetime.now() - timedelta(days=days_lookback)
                filtered_items = []
                for item in items:
                    pub_date = _parse_date(item.published_at)
                    if pub_date and pub_date >= cutoff_date:
                        filtered_items.append(item)
                items = filtered_items
            
            return items
        finally:
            db.close()
    
    try:
        return _retry_db_query(_execute_query)
    except OperationalError:
        # If database fails completely, return empty list (web search will still work)
        print("Warning: Database query failed, returning empty results. Web search will continue.")
        return []


def load_snapshots_filtered(
    country_name: Optional[str] = None,
    activity_levels: Optional[List[str]] = None,
    days_lookback: int = 90,
    limit: int = 50,
) -> List[CountrySnapshot]:
    """
    Load country snapshots with database-level filtering.
    
    Args:
        country_name: Filter by country name (case-insensitive partial match)
        activity_levels: Filter by activity levels (e.g., ["High", "Critical"])
        days_lookback: Only include snapshots updated in last N days
        limit: Maximum number of snapshots to return
    
    Returns:
        List of filtered CountrySnapshot objects
    """
    def _execute_query():
        db = SessionLocal()
        try:
            query = db.query(CountrySnapshotTable)
            
            # Filter by country name
            if country_name:
                query = query.filter(
                    CountrySnapshotTable.name.ilike(f"%{country_name}%")
                )
            
            # Filter by activity levels
            if activity_levels:
                query = query.filter(
                    CountrySnapshotTable.activity_level.in_(activity_levels)
                )
            
            # Filter by date (using updated_at_db which is a proper DateTime)
            if days_lookback > 0:
                cutoff_date = datetime.now() - timedelta(days=days_lookback)
                query = query.filter(CountrySnapshotTable.updated_at_db >= cutoff_date)
            
            # Order by activity level (Critical > High > Medium > Low) and updated_at
            # Use CASE to order by activity level priority
            activity_order = case(
                (CountrySnapshotTable.activity_level == "Critical", 1),
                (CountrySnapshotTable.activity_level == "High", 2),
                (CountrySnapshotTable.activity_level == "Medium", 3),
                (CountrySnapshotTable.activity_level == "Low", 4),
                else_=5
            )
            query = query.order_by(
                activity_order.asc(),
                CountrySnapshotTable.updated_at_db.desc()
            ).limit(limit)
            
            db_snapshots = query.all()
            return [_snapshot_to_pydantic(s) for s in db_snapshots]
        finally:
            db.close()
    
    try:
        return _retry_db_query(_execute_query)
    except OperationalError:
        # If database fails completely, return empty list (web search will still work)
        print("Warning: Database query failed, returning empty results. Web search will continue.")
        return []


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None
