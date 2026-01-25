"""Pydantic schemas for theme management."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ThemeBase(BaseModel):
    """Base theme schema."""
    name: str = Field(..., description="Theme identifier (e.g., 'sanctions')")
    display_name: str = Field(..., description="Human-readable theme name")
    keywords: List[str] = Field(default_factory=list, description="Search keywords for this theme")
    relevant_countries: Optional[List[str]] = Field(default_factory=list, description="Countries where theme is common")
    relevant_regions: Optional[List[str]] = Field(default_factory=list, description="Regions where theme is relevant")
    relevant_sectors: List[str] = Field(default_factory=list, description="Sectors exposed to this theme")
    
    # Scoring weights
    country_match_weight: float = Field(0.4, ge=0.0, le=1.0, description="Weight for country match (0.0-1.0)")
    region_match_weight: float = Field(0.2, ge=0.0, le=1.0, description="Weight for region match (0.0-1.0)")
    sector_match_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for sector match (0.0-1.0)")
    exposure_bonus_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for exposure flags (0.0-1.0)")
    emerging_market_bonus: float = Field(0.1, ge=0.0, le=1.0, description="Bonus for emerging markets (0.0-1.0)")
    min_relevance_threshold: float = Field(0.1, ge=0.0, le=1.0, description="Minimum relevance to include theme (0.0-1.0)")
    
    is_active: bool = Field(True, description="Whether this theme is active")


class ThemeCreate(ThemeBase):
    """Schema for creating a new theme."""
    pass


class ThemeUpdate(BaseModel):
    """Schema for updating a theme (all fields optional)."""
    display_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    relevant_countries: Optional[List[str]] = None
    relevant_regions: Optional[List[str]] = None
    relevant_sectors: Optional[List[str]] = None
    country_match_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    region_match_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    sector_match_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    exposure_bonus_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    emerging_market_bonus: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_relevance_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class ThemeResponse(ThemeBase):
    """Schema for theme response."""
    id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
