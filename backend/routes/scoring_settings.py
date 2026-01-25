"""API routes for scoring settings management."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..db_models import ScoringSettingsTable
from ..schemas.scoring_settings import (
    ScoringSettingsCreate,
    ScoringSettingsUpdate,
    ScoringSettingsResponse,
)
from ..scoring_settings_service import clear_scoring_settings_cache

router = APIRouter(prefix="/scoring-settings", tags=["scoring-settings"])


@router.get("", response_model=List[ScoringSettingsResponse])
def list_scoring_settings(active_only: bool = False, db: Session = Depends(get_db)):
    """List all scoring settings, optionally filtered to active only."""
    query = db.query(ScoringSettingsTable)
    if active_only:
        query = query.filter(ScoringSettingsTable.is_active == "true")
    settings = query.order_by(ScoringSettingsTable.name).all()
    
    return [
        _settings_to_response(s) for s in settings
    ]


@router.get("/{settings_name}", response_model=ScoringSettingsResponse)
def get_scoring_settings(settings_name: str, db: Session = Depends(get_db)):
    """Get a specific scoring settings by name."""
    settings = db.query(ScoringSettingsTable).filter(
        ScoringSettingsTable.name == settings_name
    ).first()
    if not settings:
        raise HTTPException(status_code=404, detail=f"Scoring settings '{settings_name}' not found")
    
    return _settings_to_response(settings)


@router.get("/active/default", response_model=ScoringSettingsResponse)
def get_active_scoring_settings(db: Session = Depends(get_db)):
    """Get the active default scoring settings."""
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
        raise HTTPException(status_code=404, detail="No active scoring settings found")
    
    return _settings_to_response(settings)


@router.post("", response_model=ScoringSettingsResponse, status_code=201)
def create_scoring_settings(settings: ScoringSettingsCreate, db: Session = Depends(get_db)):
    """Create new scoring settings."""
    existing = db.query(ScoringSettingsTable).filter(
        ScoringSettingsTable.name == settings.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Scoring settings '{settings.name}' already exists")
    
    db_settings = ScoringSettingsTable(
        name=settings.name,
        description=settings.description,
        weight_base_relevance=settings.weight_base_relevance,
        weight_theme_match=settings.weight_theme_match,
        weight_recency=settings.weight_recency,
        weight_source_quality=settings.weight_source_quality,
        weight_activity_level=settings.weight_activity_level,
        recency_decay_constant=settings.recency_decay_constant,
        score_country_exact_match=settings.score_country_exact_match,
        score_country_partial_match=settings.score_country_partial_match,
        score_region_match=settings.score_region_match,
        score_sector_match=settings.score_sector_match,
        activity_level_scores=settings.activity_level_scores or {},
        source_quality_scores=settings.source_quality_scores or {},
        semantic_threshold=settings.semantic_threshold,
        relevance_threshold_low=settings.relevance_threshold_low,
        relevance_threshold_high=settings.relevance_threshold_high,
        theme_relevance_threshold_web=settings.theme_relevance_threshold_web,
        days_lookback_default=settings.days_lookback_default,
        max_signals_default=settings.max_signals_default,
        max_events_per_snapshot=settings.max_events_per_snapshot,
        use_semantic_filtering="true" if settings.use_semantic_filtering else "false",
        is_active="true" if settings.is_active else "false",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    
    # Clear cache so new settings are used immediately
    clear_scoring_settings_cache()
    
    return _settings_to_response(db_settings)


@router.put("/{settings_name}", response_model=ScoringSettingsResponse)
def update_scoring_settings(
    settings_name: str,
    settings_update: ScoringSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update existing scoring settings."""
    settings = db.query(ScoringSettingsTable).filter(
        ScoringSettingsTable.name == settings_name
    ).first()
    if not settings:
        raise HTTPException(status_code=404, detail=f"Scoring settings '{settings_name}' not found")
    
    # Update fields if provided
    if settings_update.description is not None:
        settings.description = settings_update.description
    if settings_update.weight_base_relevance is not None:
        settings.weight_base_relevance = settings_update.weight_base_relevance
    if settings_update.weight_theme_match is not None:
        settings.weight_theme_match = settings_update.weight_theme_match
    if settings_update.weight_recency is not None:
        settings.weight_recency = settings_update.weight_recency
    if settings_update.weight_source_quality is not None:
        settings.weight_source_quality = settings_update.weight_source_quality
    if settings_update.weight_activity_level is not None:
        settings.weight_activity_level = settings_update.weight_activity_level
    if settings_update.recency_decay_constant is not None:
        settings.recency_decay_constant = settings_update.recency_decay_constant
    if settings_update.score_country_exact_match is not None:
        settings.score_country_exact_match = settings_update.score_country_exact_match
    if settings_update.score_country_partial_match is not None:
        settings.score_country_partial_match = settings_update.score_country_partial_match
    if settings_update.score_region_match is not None:
        settings.score_region_match = settings_update.score_region_match
    if settings_update.score_sector_match is not None:
        settings.score_sector_match = settings_update.score_sector_match
    if settings_update.activity_level_scores is not None:
        settings.activity_level_scores = settings_update.activity_level_scores
    if settings_update.source_quality_scores is not None:
        settings.source_quality_scores = settings_update.source_quality_scores
    if settings_update.semantic_threshold is not None:
        settings.semantic_threshold = settings_update.semantic_threshold
    if settings_update.relevance_threshold_low is not None:
        settings.relevance_threshold_low = settings_update.relevance_threshold_low
    if settings_update.relevance_threshold_high is not None:
        settings.relevance_threshold_high = settings_update.relevance_threshold_high
    if settings_update.theme_relevance_threshold_web is not None:
        settings.theme_relevance_threshold_web = settings_update.theme_relevance_threshold_web
    if settings_update.days_lookback_default is not None:
        settings.days_lookback_default = settings_update.days_lookback_default
    if settings_update.max_signals_default is not None:
        settings.max_signals_default = settings_update.max_signals_default
    if settings_update.max_events_per_snapshot is not None:
        settings.max_events_per_snapshot = settings_update.max_events_per_snapshot
    if settings_update.use_semantic_filtering is not None:
        settings.use_semantic_filtering = "true" if settings_update.use_semantic_filtering else "false"
    if settings_update.is_active is not None:
        settings.is_active = "true" if settings_update.is_active else "false"
    
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    
    return _settings_to_response(settings)


def _settings_to_response(settings: ScoringSettingsTable) -> ScoringSettingsResponse:
    """Convert database model to response schema."""
    return ScoringSettingsResponse(
        id=settings.id,
        name=settings.name,
        description=settings.description,
        weight_base_relevance=settings.weight_base_relevance,
        weight_theme_match=settings.weight_theme_match,
        weight_recency=settings.weight_recency,
        weight_source_quality=settings.weight_source_quality,
        weight_activity_level=settings.weight_activity_level,
        recency_decay_constant=settings.recency_decay_constant,
        score_country_exact_match=settings.score_country_exact_match,
        score_country_partial_match=settings.score_country_partial_match,
        score_region_match=settings.score_region_match,
        score_sector_match=settings.score_sector_match,
        activity_level_scores=settings.activity_level_scores or {},
        source_quality_scores=settings.source_quality_scores or {},
        semantic_threshold=settings.semantic_threshold,
        relevance_threshold_low=settings.relevance_threshold_low,
        relevance_threshold_high=settings.relevance_threshold_high,
        theme_relevance_threshold_web=settings.theme_relevance_threshold_web,
        days_lookback_default=settings.days_lookback_default,
        max_signals_default=settings.max_signals_default,
        max_events_per_snapshot=settings.max_events_per_snapshot,
        use_semantic_filtering=settings.use_semantic_filtering == "true",
        is_active=settings.is_active == "true",
        created_at=settings.created_at.isoformat() if settings.created_at else "",
        updated_at=settings.updated_at.isoformat() if settings.updated_at else "",
    )
