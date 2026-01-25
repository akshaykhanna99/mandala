"""SQLAlchemy database models."""
from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class SourceRefTable(Base):
    """Stores source references (embedded in other tables via JSON)."""
    __tablename__ = "source_refs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)


class CountrySnapshotTable(Base):
    """Country snapshots with events and stats."""
    __tablename__ = "country_snapshots"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    activity_level = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    events = Column(JSON, nullable=False)  # List of EventCluster objects
    stats = Column(JSON, nullable=False)  # CountryStats object
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at_db = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GlobalItemTable(Base):
    """Global news items from various sources."""
    __tablename__ = "global_items"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    source = Column(JSON, nullable=False)  # SourceRef object
    url = Column(String, nullable=False, unique=True, index=True)
    published_at = Column(String, nullable=False)
    topic = Column(String, nullable=False, index=True)
    countries = Column(ARRAY(String), nullable=False)
    country_ids = Column(ARRAY(String), nullable=False, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketItemTable(Base):
    """Market data items."""
    __tablename__ = "market_items"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False, unique=True, index=True)
    category = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    change = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)
    updated_at = Column(String, nullable=False)
    source = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at_db = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ThemeTable(Base):
    """Customizable geopolitical themes."""
    __tablename__ = "themes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)  # e.g., "sanctions"
    display_name = Column(String, nullable=False)  # e.g., "Sanctions"
    keywords = Column(ARRAY(String), nullable=False, default=[])  # Search keywords
    relevant_countries = Column(ARRAY(String), nullable=True, default=[])  # Countries where theme is common
    relevant_regions = Column(ARRAY(String), nullable=True, default=[])  # Regions where theme is relevant
    relevant_sectors = Column(ARRAY(String), nullable=False, default=[])  # Sectors exposed to this theme
    
    # Scoring weights (0.0 to 1.0)
    country_match_weight = Column(Float, nullable=False, default=0.4)  # Weight for country match
    region_match_weight = Column(Float, nullable=False, default=0.2)  # Weight for region match
    sector_match_weight = Column(Float, nullable=False, default=0.3)  # Weight for sector match
    exposure_bonus_weight = Column(Float, nullable=False, default=0.3)  # Weight for exposure flags
    emerging_market_bonus = Column(Float, nullable=False, default=0.1)  # Bonus for emerging markets
    
    # Minimum relevance threshold (0.0 to 1.0)
    min_relevance_threshold = Column(Float, nullable=False, default=0.1)  # Only include if score >= this
    
    is_active = Column(String, nullable=False, default="true")  # "true" or "false" (using String for simplicity)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScoringSettingsTable(Base):
    """Global scoring system settings."""
    __tablename__ = "scoring_settings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)  # e.g., "default"
    description = Column(String, nullable=True)
    
    # Scoring weights (must sum to 1.0)
    weight_base_relevance = Column(Float, nullable=False, default=0.3)
    weight_theme_match = Column(Float, nullable=False, default=0.25)
    weight_recency = Column(Float, nullable=False, default=0.2)
    weight_source_quality = Column(Float, nullable=False, default=0.15)
    weight_activity_level = Column(Float, nullable=False, default=0.1)
    
    # Recency decay
    recency_decay_constant = Column(Float, nullable=False, default=30.0)  # Half-life ~21 days
    
    # Base relevance scores
    score_country_exact_match = Column(Float, nullable=False, default=0.5)
    score_country_partial_match = Column(Float, nullable=False, default=0.3)
    score_region_match = Column(Float, nullable=False, default=0.2)
    score_sector_match = Column(Float, nullable=False, default=0.2)
    
    # Activity level scores (stored as JSON for flexibility)
    activity_level_scores = Column(JSON, nullable=False, default={
        "Critical": 1.0,
        "High": 0.8,
        "Medium": 0.5,
        "Low": 0.2,
        "default": 0.3,
    })
    
    # Source quality scores (stored as JSON: {"source_name": score})
    source_quality_scores = Column(JSON, nullable=False, default={
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
    })
    
    # Thresholds
    semantic_threshold = Column(Float, nullable=False, default=0.6)  # Claude semantic relevance threshold
    relevance_threshold_low = Column(Float, nullable=False, default=0.05)  # When <5 signals
    relevance_threshold_high = Column(Float, nullable=False, default=0.1)  # When >=5 signals
    theme_relevance_threshold_web = Column(Float, nullable=False, default=0.3)  # For web search theme filtering
    
    # Pipeline parameters
    days_lookback_default = Column(Integer, nullable=False, default=90)
    max_signals_default = Column(Integer, nullable=False, default=20)
    max_events_per_snapshot = Column(Integer, nullable=False, default=3)
    
    # Semantic filtering
    use_semantic_filtering = Column(String, nullable=False, default="true")  # "true" or "false"
    
    is_active = Column(String, nullable=False, default="true")  # "true" or "false"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AssetTable(Base):
    """Stores asset information."""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    ticker = Column(String, nullable=True, index=True)
    isin = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True, index=True)
    region = Column(String, nullable=False)
    sub_region = Column(String, nullable=True)
    asset_type = Column(String, nullable=False)  # e.g., "Equity", "Bond", "Commodity"
    asset_class = Column(String, nullable=False)  # e.g., "Equities", "Fixed Income", "Commodities"
    sector = Column(String, nullable=False, index=True)
    is_emerging_market = Column(String, nullable=False, default="false")  # "true" or "false"
    is_developed_market = Column(String, nullable=False, default="false")  # "true" or "false"
    is_global_fund = Column(String, nullable=False, default="false")  # "true" or "false"
    exposures = Column(ARRAY(String), nullable=False, default=[])  # ["Government", "Energy", etc.]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GPScanTable(Base):
    """Stores GP (Geopolitical) risk scan results."""
    __tablename__ = "gp_scans"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Scan metadata
    risk_tolerance = Column(String, nullable=False)  # "Low", "Medium", "High"
    days_lookback = Column(Integer, nullable=False, default=90)
    scan_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Full pipeline result (stored as JSON)
    pipeline_result = Column(JSON, nullable=False)  # Complete DetailedPipelineResult
    
    # Key metrics (for quick querying)
    negative_probability = Column(Float, nullable=False)  # Sell probability
    neutral_probability = Column(Float, nullable=False)    # Hold probability
    positive_probability = Column(Float, nullable=False)    # Buy probability
    overall_direction = Column(String, nullable=False)     # "negative", "neutral", "positive"
    overall_magnitude = Column(Float, nullable=False)     # 0.0 to 1.0
    confidence = Column(Float, nullable=False)             # 0.0 to 1.0
    signal_count = Column(Integer, nullable=False, default=0)
    top_themes = Column(ARRAY(String), nullable=False, default=[])  # Top 5 themes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
