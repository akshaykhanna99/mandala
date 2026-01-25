"""Seed default scoring settings into the database."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    exit(1)

# Convert postgresql:// to postgresql+psycopg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

default_activity_scores = {
    "Critical": 1.0,
    "High": 0.8,
    "Medium": 0.5,
    "Low": 0.2,
    "default": 0.3,
}

default_source_scores = {
    "Reuters": 1.0,
    "BBC": 1.0,
    "Financial Times": 0.95,
    "The Guardian": 0.9,
    "The New York Times": 0.95,
    "The Wall Street Journal": 0.95,
    "Bloomberg": 0.9,
    "Associated Press": 0.95,
    "Al Jazeera": 0.85,
    "CNN": 0.85,
    "The Economist": 0.9,
    "Foreign Policy": 0.85,
    "Foreign Affairs": 0.85,
    "The Diplomat": 0.8,
    "default": 0.7,
}

def seed_scoring_settings():
    """Seed default scoring settings into database."""
    db = SessionLocal()
    try:
        from backend.db_models import ScoringSettingsTable
        from datetime import datetime
        
        # Check if default settings already exist
        existing = db.query(ScoringSettingsTable).filter(ScoringSettingsTable.name == "default").first()
        if existing:
            print("⏭️  Default scoring settings already exist, skipping")
            return
        
        settings = ScoringSettingsTable(
            name="default",
            description="Default scoring configuration",
            weight_base_relevance=0.3,
            weight_theme_match=0.25,
            weight_recency=0.2,
            weight_source_quality=0.15,
            weight_activity_level=0.1,
            recency_decay_constant=30.0,
            score_country_exact_match=0.5,
            score_country_partial_match=0.3,
            score_region_match=0.2,
            score_sector_match=0.2,
            activity_level_scores=default_activity_scores,
            source_quality_scores=default_source_scores,
            semantic_threshold=0.6,
            relevance_threshold_low=0.05,
            relevance_threshold_high=0.1,
            theme_relevance_threshold_web=0.3,
            days_lookback_default=90,
            max_signals_default=20,
            max_events_per_snapshot=3,
            use_semantic_filtering="true",
            is_active="true",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(settings)
        db.commit()
        print("✅ Default scoring settings seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding scoring settings: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_scoring_settings()
