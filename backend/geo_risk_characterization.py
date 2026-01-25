"""Asset characterization pipeline for geopolitical risk analysis."""
from dataclasses import dataclass
from typing import List, Set
from .schemas.geo_risk import Holding


@dataclass
class AssetProfile:
    """Structured profile of an asset for geopolitical risk analysis."""
    # Core identifiers
    id: str
    name: str
    ticker: str | None
    isin: str | None
    
    # Geographic exposure
    country: str | None
    region: str
    sub_region: str | None
    
    # Asset classification
    asset_type: str  # Equity, Fixed Income, Alternative, etc.
    asset_class: str  # Equities, Fixed Income, Alternatives, etc.
    sector: str
    
    # Financial metrics
    value: float
    allocation_pct: float
    
    # Derived characteristics
    is_emerging_market: bool
    is_developed_market: bool
    is_global_fund: bool
    is_sector_specific: bool
    is_country_specific: bool
    
    # Risk-relevant flags
    is_government_exposed: bool  # Government bonds, state-owned enterprises
    is_energy_exposed: bool  # Energy sector or energy-dependent
    is_financial_exposed: bool  # Financial sector
    is_technology_exposed: bool  # Technology sector
    is_infrastructure_exposed: bool  # Infrastructure/utilities


def characterize_asset(holding: Holding) -> AssetProfile:
    """
    Extract and structure asset characteristics for geopolitical risk analysis.
    
    Args:
        holding: Investment holding with metadata
    
    Returns:
        AssetProfile with all relevant characteristics
    """
    # Determine market classification
    emerging_markets = {
        "Turkey", "China", "India", "Brazil", "Russia", "South Africa",
        "Mexico", "Indonesia", "Thailand", "Philippines", "Vietnam",
        "Argentina", "Chile", "Colombia", "Egypt", "Nigeria", "Pakistan",
        "Poland", "Czech Republic", "Hungary", "Romania", "Bulgaria",
    }
    
    developed_markets = {
        "United States", "United Kingdom", "Germany", "France", "Japan",
        "Canada", "Australia", "Switzerland", "Netherlands", "Sweden",
        "Norway", "Denmark", "Finland", "Belgium", "Austria", "Italy",
        "Spain", "Singapore", "Hong Kong", "South Korea", "New Zealand",
    }
    
    country = holding.country or ""
    is_emerging = country in emerging_markets
    is_developed = country in developed_markets
    is_global = not country or country == "Global" or holding.region == "Global"
    
    # Sector classification
    energy_sectors = {"Energy", "Oil", "Gas", "Utilities"}
    financial_sectors = {"Financials", "Banking", "Insurance"}
    tech_sectors = {"Technology", "Software", "Hardware", "Semiconductors"}
    infrastructure_sectors = {"Infrastructure", "Utilities", "Transportation", "Real Estate"}
    government_sectors = {"Government", "Sovereign"}
    
    is_energy = holding.sector in energy_sectors
    is_financial = holding.sector in financial_sectors
    is_technology = holding.sector in tech_sectors
    is_infrastructure = holding.sector in infrastructure_sectors
    is_government = (
        holding.sector in government_sectors or
        holding.class_ == "Fixed Income" and "Treasury" in holding.name or
        "Government" in holding.name
    )
    
    # Determine specificity
    is_sector_specific = holding.sector not in {"Diversified", "Cash", "General"}
    is_country_specific = bool(country and country != "Global")
    
    return AssetProfile(
        id=holding.id,
        name=holding.name,
        ticker=holding.ticker,
        isin=holding.isin,
        country=holding.country,
        region=holding.region,
        sub_region=holding.sub_region,
        asset_type=holding.class_,  # Use class instead of type
        asset_class=holding.class_,
        sector=holding.sector,
        value=holding.value,
        allocation_pct=holding.allocation_pct,
        is_emerging_market=is_emerging,
        is_developed_market=is_developed,
        is_global_fund=is_global,
        is_sector_specific=is_sector_specific,
        is_country_specific=is_country_specific,
        is_government_exposed=is_government,
        is_energy_exposed=is_energy,
        is_financial_exposed=is_financial,
        is_technology_exposed=is_technology,
        is_infrastructure_exposed=is_infrastructure,
    )


def get_characterization_summary(profile: AssetProfile) -> str:
    """
    Generate a human-readable summary of asset characteristics.
    
    Useful for LLM prompts and logging.
    """
    parts = []
    
    if profile.country:
        parts.append(f"Country: {profile.country}")
    parts.append(f"Region: {profile.region}")
    if profile.sub_region:
        parts.append(f"Sub-region: {profile.sub_region}")
    
    parts.append(f"Type: {profile.asset_type}")
    parts.append(f"Class: {profile.asset_class}")
    parts.append(f"Sector: {profile.sector}")
    
    if profile.is_emerging_market:
        parts.append("Market: Emerging")
    elif profile.is_developed_market:
        parts.append("Market: Developed")
    elif profile.is_global_fund:
        parts.append("Market: Global")
    
    exposures = []
    if profile.is_government_exposed:
        exposures.append("Government")
    if profile.is_energy_exposed:
        exposures.append("Energy")
    if profile.is_financial_exposed:
        exposures.append("Financial")
    if profile.is_technology_exposed:
        exposures.append("Technology")
    if profile.is_infrastructure_exposed:
        exposures.append("Infrastructure")
    
    if exposures:
        parts.append(f"Exposures: {', '.join(exposures)}")
    
    return " | ".join(parts)
