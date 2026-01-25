"""Pydantic schemas for Geopolitical Health Scan."""
from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field


class Holding(BaseModel):
    """Portfolio holding with detailed properties."""
    id: str
    name: str
    class_: str = Field(..., alias="class", description="Asset class: Equities, Fixed Income, Alternatives, etc.")
    region: str
    sector: str
    value: float
    allocation_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of portfolio")
    pnl_to_date: float = Field(default=0.0, description="Profit/Loss to date")
    pnl_pct: float = Field(default=0.0, description="PnL as percentage")
    currency: str = Field(default="USD")
    entry_date: str | None = Field(default=None, description="YYYY-MM-DD")
    last_valuation_date: str | None = Field(default=None, description="YYYY-MM-DD")
    ticker: str | None = Field(default=None, description="Ticker symbol for publicly traded securities")
    isin: str | None = Field(default=None, description="International Securities Identification Number")
    country: str | None = Field(default=None, description="Specific country if applicable")
    sub_region: str | None = Field(default=None, description="Sub-region e.g., Western Europe")
    gp_score: dict | None = Field(
        default=None,
        description="Geopolitical risk score with Sell/Hold/Buy probabilities"
    )
    
    class Config:
        populate_by_name = True


class Portfolio(BaseModel):
    """Client portfolio structure."""
    total_value: float
    holdings: List[Holding]


class GeoRiskScanInputs(BaseModel):
    """Inputs for a geopolitical risk scan."""
    client_id: str
    as_of: str = Field(..., description="YYYY-MM-DD format")
    horizon_days: int = Field(..., ge=1, le=3650)
    risk_tolerance: Literal["low", "medium", "high"]
    portfolio: Portfolio


class Scenario(BaseModel):
    """Risk scenario with probability."""
    name: Literal["low", "moderate", "severe"]
    p: float = Field(..., ge=0.0, le=1.0, description="Probability (0-1)")


class Citation(BaseModel):
    """Regulatory citation reference."""
    doc_id: str = Field(default="FCA_EXCERPTS")
    snippet_id: str
    section: str


class GeoRiskOutput(BaseModel):
    """Geopolitical risk assessment output."""
    scenarios: List[Scenario] = Field(..., min_length=3, max_length=3)
    confidence: Literal["low", "medium", "high"]
    drivers: List[str] = Field(..., min_length=1, max_length=10)
    suitability_impact: str = Field(..., min_length=50, max_length=500)
    limitations: List[str] = Field(..., min_length=1, max_length=5)
    disclaimer: str = "Internal decision-support only. Not financial advice."
    citations: List[Citation] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Validation metadata."""
    passed: bool
    errors: List[str] = Field(default_factory=list)


class GeoRiskScanMeta(BaseModel):
    """Metadata about the scan."""
    model: str
    used_fallback: bool = False
    validation: ValidationResult


class GeoRiskScanResult(BaseModel):
    """Complete geopolitical risk scan result."""
    scan_id: str
    created_at: str  # ISO8601 format
    inputs: GeoRiskScanInputs
    geo_risk: GeoRiskOutput
    meta: GeoRiskScanMeta


class GeoRiskScanRequest(BaseModel):
    """Request payload for POST /geo-risk/scan."""
    client_id: str
    as_of: str = Field(..., description="YYYY-MM-DD format")
    horizon_days: int = Field(default=365, ge=1, le=3650)
    risk_tolerance: Literal["low", "medium", "high"]
    portfolio: Portfolio


# Detailed pipeline response schemas
class ThemeDetail(BaseModel):
    """Theme identification detail."""
    theme: str
    relevance_score: float
    reasoning: str
    keywords_matched: List[str]


class IntelligenceSignalDetail(BaseModel):
    """Intelligence signal detail."""
    source: str
    title: str
    summary: str
    topic: str
    relevance_score: float
    theme_match: str | None
    published_at: str
    url: str | None = None
    country: str | None = None
    activity_level: str | None = None
    base_relevance: float = 0.0
    theme_match_score: float = 0.0
    recency_score: float = 0.0
    source_quality: float = 0.0
    activity_level_score: float = 0.0


class ThemeImpactDetail(BaseModel):
    """Theme impact assessment detail."""
    theme: str
    impact_direction: str
    impact_magnitude: float
    confidence: float
    reasoning: str
    signal_count: int
    summary: str = ""


class AggregateImpactDetail(BaseModel):
    """Aggregate impact assessment detail."""
    overall_direction: str
    overall_magnitude: float
    confidence: float
    theme_impacts: List[ThemeImpactDetail]
    total_signals: int


class ActionProbabilitiesDetail(BaseModel):
    """Action probabilities detail."""
    sell: float
    hold: float
    buy: float


class WebSearchDetail(BaseModel):
    """Web search metadata for a theme."""
    theme: str
    query: str
    results_count: int
    signals_count: int
    error: str | None = None


class DetailedPipelineResult(BaseModel):
    """Detailed pipeline result with all intermediate steps."""
    # Step 1: Characterization
    characterization_summary: str
    asset_country: str | None
    asset_region: str
    asset_sub_region: str | None
    asset_type: str
    asset_class: str
    asset_sector: str
    is_emerging_market: bool
    is_developed_market: bool
    is_global_fund: bool
    exposures: List[str]
    
    # Step 2: Theme identification
    themes: List[ThemeDetail]
    top_themes: List[str]
    
    # Step 3: Intelligence retrieval
    signals: List[IntelligenceSignalDetail]
    signal_count: int
    web_searches: List[WebSearchDetail]  # Web search metadata
    
    # Step 4: Impact assessment
    impact: AggregateImpactDetail
    
    # Step 5: Probability calculation
    probabilities: ActionProbabilitiesDetail
    probability_summary: str
    
    # Metadata
    risk_tolerance: str
    days_lookback: int
