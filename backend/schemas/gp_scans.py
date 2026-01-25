"""Pydantic schemas for GP scan management."""
from typing import Optional
from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    """Schema for creating a new asset."""
    name: str
    ticker: Optional[str] = None
    isin: Optional[str] = None
    country: Optional[str] = None
    region: str
    sub_region: Optional[str] = None
    asset_type: str
    asset_class: str
    sector: str
    is_emerging_market: bool = False
    is_developed_market: bool = False
    is_global_fund: bool = False
    exposures: list[str] = Field(default_factory=list)


class AssetResponse(BaseModel):
    """Schema for asset response."""
    id: int
    name: str
    ticker: Optional[str] = None
    isin: Optional[str] = None
    country: Optional[str] = None
    region: str
    sub_region: Optional[str] = None
    asset_type: str
    asset_class: str
    sector: str
    is_emerging_market: bool
    is_developed_market: bool
    is_global_fund: bool
    exposures: list[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class GPScanCreate(BaseModel):
    """Schema for creating a new GP scan."""
    asset_id: Optional[int] = None  # If None, asset will be created from pipeline result
    risk_tolerance: str
    days_lookback: int = 90
    pipeline_result: dict  # Full DetailedPipelineResult as dict


class GPScanResponse(BaseModel):
    """Schema for GP scan response."""
    id: int
    asset_id: int
    risk_tolerance: str
    days_lookback: int
    scan_date: str
    negative_probability: float
    neutral_probability: float
    positive_probability: float
    overall_direction: str
    overall_magnitude: float
    confidence: float
    signal_count: int
    top_themes: list[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
