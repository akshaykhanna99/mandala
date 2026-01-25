"""Pydantic schemas for scoring settings management."""
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ScoringSettingsBase(BaseModel):
    """Base scoring settings schema."""
    name: str = Field(..., description="Settings name (e.g., 'default')")
    description: Optional[str] = Field(None, description="Description of these settings")
    
    # Scoring weights (should sum to 1.0)
    weight_base_relevance: float = Field(0.3, ge=0.0, le=1.0)
    weight_theme_match: float = Field(0.25, ge=0.0, le=1.0)
    weight_recency: float = Field(0.2, ge=0.0, le=1.0)
    weight_source_quality: float = Field(0.15, ge=0.0, le=1.0)
    weight_activity_level: float = Field(0.1, ge=0.0, le=1.0)
    
    # Recency decay
    recency_decay_constant: float = Field(30.0, gt=0.0, description="Decay constant for recency (higher = slower decay)")
    
    # Base relevance scores
    score_country_exact_match: float = Field(0.5, ge=0.0, le=1.0)
    score_country_partial_match: float = Field(0.3, ge=0.0, le=1.0)
    score_region_match: float = Field(0.2, ge=0.0, le=1.0)
    score_sector_match: float = Field(0.2, ge=0.0, le=1.0)
    
    # Activity level scores (JSON dict)
    activity_level_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Source quality scores (JSON dict)
    source_quality_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Thresholds
    semantic_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Claude semantic relevance threshold")
    relevance_threshold_low: float = Field(0.05, ge=0.0, le=1.0, description="Relevance threshold when <5 signals")
    relevance_threshold_high: float = Field(0.1, ge=0.0, le=1.0, description="Relevance threshold when >=5 signals")
    theme_relevance_threshold_web: float = Field(0.3, ge=0.0, le=1.0, description="Theme relevance threshold for web search")
    
    # Pipeline parameters
    days_lookback_default: int = Field(90, ge=1, le=365)
    max_signals_default: int = Field(20, ge=1, le=100)
    max_events_per_snapshot: int = Field(3, ge=1, le=10)
    
    # Semantic filtering
    use_semantic_filtering: bool = Field(True, description="Enable Claude semantic filtering")
    
    is_active: bool = Field(True)


class ScoringSettingsCreate(ScoringSettingsBase):
    """Schema for creating new scoring settings."""
    pass


class ScoringSettingsUpdate(BaseModel):
    """Schema for updating scoring settings (all fields optional)."""
    description: Optional[str] = None
    weight_base_relevance: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_theme_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_recency: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_source_quality: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_activity_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    recency_decay_constant: Optional[float] = Field(None, gt=0.0)
    score_country_exact_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    score_country_partial_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    score_region_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    score_sector_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    activity_level_scores: Optional[Dict[str, float]] = None
    source_quality_scores: Optional[Dict[str, float]] = None
    semantic_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance_threshold_low: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance_threshold_high: Optional[float] = Field(None, ge=0.0, le=1.0)
    theme_relevance_threshold_web: Optional[float] = Field(None, ge=0.0, le=1.0)
    days_lookback_default: Optional[int] = Field(None, ge=1, le=365)
    max_signals_default: Optional[int] = Field(None, ge=1, le=100)
    max_events_per_snapshot: Optional[int] = Field(None, ge=1, le=10)
    use_semantic_filtering: Optional[bool] = None
    is_active: Optional[bool] = None


class ScoringSettingsResponse(ScoringSettingsBase):
    """Schema for scoring settings response."""
    id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
