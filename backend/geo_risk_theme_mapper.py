"""Theme identification - maps asset characteristics to relevant geopolitical themes."""
from dataclasses import dataclass
from typing import List, Dict, Optional
from .geo_risk_characterization import AssetProfile
from .theme_store import load_themes_from_db, get_theme_weights_from_db


# Default geopolitical theme definitions (fallback if database is empty)
DEFAULT_GEOPOLITICAL_THEMES = {
    "sanctions": {
        "keywords": ["sanction", "embargo", "trade ban", "restriction"],
        "relevant_countries": ["Russia", "Iran", "North Korea", "Turkey", "China"],
        "relevant_sectors": ["Financials", "Energy", "Technology", "Defense"],
    },
    "trade_disruption": {
        "keywords": ["trade war", "tariff", "export ban", "import restriction", "supply chain"],
        "relevant_countries": ["China", "United States", "Turkey", "Russia"],
        "relevant_sectors": ["Technology", "Manufacturing", "Energy", "Agriculture"],
    },
    "political_instability": {
        "keywords": ["coup", "election", "protest", "unrest", "regime change"],
        "relevant_countries": ["Turkey", "Thailand", "Egypt", "Venezuela", "Pakistan"],
        "relevant_sectors": ["Financials", "Infrastructure", "Government"],
    },
    "currency_volatility": {
        "keywords": ["currency", "inflation", "devaluation", "exchange rate", "monetary policy"],
        "relevant_countries": ["Turkey", "Argentina", "Brazil", "South Africa", "India"],
        "relevant_sectors": ["Financials", "Government"],
    },
    "energy_security": {
        "keywords": ["energy", "oil", "gas", "pipeline", "supply", "sanction"],
        "relevant_countries": ["Russia", "Saudi Arabia", "Iran", "Turkey", "Qatar"],
        "relevant_sectors": ["Energy", "Utilities", "Infrastructure"],
    },
    "regional_conflict": {
        "keywords": ["conflict", "war", "military", "border", "dispute", "tension"],
        "relevant_regions": ["Middle East", "Eastern Europe", "Asia Pacific", "Emerging Markets"],
        "relevant_sectors": ["Defense", "Energy", "Infrastructure"],
    },
    "regulatory_changes": {
        "keywords": ["regulation", "policy", "law", "compliance", "government"],
        "relevant_countries": ["China", "United States", "European Union"],
        "relevant_sectors": ["Financials", "Technology", "Energy", "Healthcare"],
    },
    "supply_chain_risk": {
        "keywords": ["supply chain", "manufacturing", "logistics", "trade"],
        "relevant_countries": ["China", "Vietnam", "Thailand", "Mexico"],
        "relevant_sectors": ["Technology", "Manufacturing", "Consumer"],
    },
}


def get_geopolitical_themes() -> Dict[str, Dict]:
    """
    Get geopolitical themes from database, with fallback to defaults.
    
    Returns a dictionary of theme definitions.
    """
    db_themes = load_themes_from_db()
    if db_themes:
        return db_themes
    return DEFAULT_GEOPOLITICAL_THEMES


@dataclass
class ThemeRelevance:
    """Theme with relevance score for an asset."""
    theme: str
    relevance_score: float  # 0.0 to 1.0
    reasoning: str
    keywords_matched: List[str]


def identify_relevant_themes(profile: AssetProfile) -> List[ThemeRelevance]:
    """
    Identify which geopolitical themes are relevant to this asset.
    
    Uses themes from database if available, otherwise falls back to defaults.
    Uses customizable scoring weights from database.
    
    Returns themes sorted by relevance (highest first).
    """
    relevant_themes: List[ThemeRelevance] = []
    themes = get_geopolitical_themes()
    
    for theme_name, theme_def in themes.items():
        # Get custom weights for this theme (or use defaults)
        weights = get_theme_weights_from_db(theme_name)
        country_weight = weights["country_match_weight"] if weights else theme_def.get("country_match_weight", 0.4)
        region_weight = weights["region_match_weight"] if weights else theme_def.get("region_match_weight", 0.2)
        sector_weight = weights["sector_match_weight"] if weights else theme_def.get("sector_match_weight", 0.3)
        exposure_weight = weights["exposure_bonus_weight"] if weights else theme_def.get("exposure_bonus_weight", 0.3)
        emerging_bonus = weights["emerging_market_bonus"] if weights else theme_def.get("emerging_market_bonus", 0.1)
        min_threshold = weights["min_relevance_threshold"] if weights else theme_def.get("min_relevance_threshold", 0.1)
        
        score = 0.0
        reasoning_parts = []
        matched_keywords = []
        
        # Check country match
        if profile.country:
            if profile.country in theme_def.get("relevant_countries", []):
                score += country_weight
                reasoning_parts.append(f"Country {profile.country} is directly relevant")
        
        # Check region match
        if profile.region in theme_def.get("relevant_regions", []):
            score += region_weight
            reasoning_parts.append(f"Region {profile.region} is relevant")
        
        # Check sector match
        if profile.sector in theme_def.get("relevant_sectors", []):
            score += sector_weight
            reasoning_parts.append(f"Sector {profile.sector} is exposed")
        
        # Check exposure flags (using customizable weight)
        if theme_name == "energy_security" and profile.is_energy_exposed:
            score += exposure_weight
            reasoning_parts.append("Energy sector exposure")
        
        if theme_name == "currency_volatility" and profile.is_financial_exposed:
            score += exposure_weight * 0.67  # Scale down for financial exposure
            reasoning_parts.append("Financial sector exposure")
        
        if theme_name == "political_instability" and profile.is_government_exposed:
            score += exposure_weight
            reasoning_parts.append("Government exposure")
        
        if theme_name == "supply_chain_risk" and profile.is_technology_exposed:
            score += exposure_weight * 0.67  # Scale down for tech exposure
            reasoning_parts.append("Technology sector exposure")
        
        # Emerging market bonus for certain themes
        if profile.is_emerging_market:
            if theme_name in ["currency_volatility", "political_instability", "trade_disruption"]:
                score += emerging_bonus
                reasoning_parts.append("Emerging market context")
        
        # Normalize score to 0-1 range
        score = min(1.0, score)
        
        # Use customizable threshold
        if score >= min_threshold:
            # Create more readable reasoning
            readable_reasoning = _create_readable_reasoning(
                reasoning_parts, profile, theme_name
            )
            
            relevant_themes.append(
                ThemeRelevance(
                    theme=theme_name,
                    relevance_score=score,
                    reasoning=readable_reasoning,
                    keywords_matched=matched_keywords,
                )
            )
    
    # Sort by relevance score (highest first)
    relevant_themes.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return relevant_themes


def _create_readable_reasoning(reasoning_parts: List[str], profile: AssetProfile, theme_name: str) -> str:
    """Create human-readable reasoning from technical parts."""
    if not reasoning_parts:
        return "General relevance to this asset"
    
    # Format theme name
    theme_display = theme_name.replace("_", " ").title()
    
    # Build readable sentences
    sentences = []
    
    # Country/region context
    if profile.country:
        sentences.append(f"This asset is exposed to {profile.country}")
    elif profile.region:
        sentences.append(f"This asset is located in {profile.region}")
    
    # Sector context
    if profile.sector and profile.sector not in ["Diversified", "Cash"]:
        sentences.append(f"operating in the {profile.sector} sector")
    
    # Theme-specific context
    if "Country" in " ".join(reasoning_parts):
        sentences.append(f"which makes it particularly vulnerable to {theme_display}")
    elif "Sector" in " ".join(reasoning_parts):
        sentences.append(f"which is directly impacted by {theme_display}")
    elif "Emerging market" in " ".join(reasoning_parts):
        sentences.append(f"with emerging market exposure increasing {theme_display} risk")
    else:
        sentences.append(f"relevant to {theme_display} considerations")
    
    # Combine into readable text
    if len(sentences) == 1:
        return sentences[0] + "."
    elif len(sentences) == 2:
        return " ".join(sentences) + "."
    else:
        # First sentence, then list others
        return sentences[0] + ". " + " ".join(sentences[1:]) + "."


def get_top_themes(profile: AssetProfile, max_themes: int = 5) -> List[str]:
    """
    Get the top N most relevant themes for an asset.
    
    Returns just the theme names.
    """
    themes = identify_relevant_themes(profile)
    return [t.theme for t in themes[:max_themes]]
