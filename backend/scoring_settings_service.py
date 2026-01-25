"""Service to load and cache scoring settings from database."""
from typing import Dict, Optional
from functools import lru_cache
from .database import SessionLocal
from .db_models import ScoringSettingsTable


@lru_cache(maxsize=1)
def get_active_scoring_settings() -> Optional[Dict]:
    """Get active scoring settings from database with caching."""
    db = SessionLocal()
    try:
        settings = db.query(ScoringSettingsTable).filter(
            ScoringSettingsTable.is_active == "true",
            ScoringSettingsTable.name == "default"
        ).first()
        
        if not settings:
            # Fallback: get any active settings
            settings = db.query(ScoringSettingsTable).filter(
                ScoringSettingsTable.is_active == "true"
            ).first()
        
        if not settings:
            return None
        
        return {
            "weight_base_relevance": settings.weight_base_relevance,
            "weight_theme_match": settings.weight_theme_match,
            "weight_recency": settings.weight_recency,
            "weight_source_quality": settings.weight_source_quality,
            "weight_activity_level": settings.weight_activity_level,
            "recency_decay_constant": settings.recency_decay_constant,
            "score_country_exact_match": settings.score_country_exact_match,
            "score_country_partial_match": settings.score_country_partial_match,
            "score_region_match": settings.score_region_match,
            "score_sector_match": settings.score_sector_match,
            "activity_level_scores": settings.activity_level_scores or {},
            "source_quality_scores": settings.source_quality_scores or {},
            "semantic_threshold": settings.semantic_threshold,
            "relevance_threshold_low": settings.relevance_threshold_low,
            "relevance_threshold_high": settings.relevance_threshold_high,
            "theme_relevance_threshold_web": settings.theme_relevance_threshold_web,
            "days_lookback_default": settings.days_lookback_default,
            "max_signals_default": settings.max_signals_default,
            "max_events_per_snapshot": settings.max_events_per_snapshot,
            "use_semantic_filtering": settings.use_semantic_filtering == "true",
        }
    except Exception as e:
        print(f"Error loading scoring settings: {e}")
        return None
    finally:
        db.close()


def clear_scoring_settings_cache():
    """Clear the scoring settings cache (call after updating settings)."""
    get_active_scoring_settings.cache_clear()
