"""Load themes from database with fallback to defaults."""
from typing import Dict, List, Optional
from .database import SessionLocal
from .db_models import ThemeTable


def load_themes_from_db() -> Optional[Dict[str, Dict]]:
    """Load themes from database. Returns None if no themes found."""
    db = SessionLocal()
    try:
        themes = db.query(ThemeTable).filter(ThemeTable.is_active == "true").all()
        if not themes:
            return None
        
        themes_dict = {}
        for theme in themes:
            themes_dict[theme.name] = {
                "keywords": theme.keywords or [],
                "relevant_countries": theme.relevant_countries or [],
                "relevant_regions": theme.relevant_regions or [],
                "relevant_sectors": theme.relevant_sectors or [],
                "country_match_weight": theme.country_match_weight,
                "region_match_weight": theme.region_match_weight,
                "sector_match_weight": theme.sector_match_weight,
                "exposure_bonus_weight": theme.exposure_bonus_weight,
                "emerging_market_bonus": theme.emerging_market_bonus,
                "min_relevance_threshold": theme.min_relevance_threshold,
            }
        return themes_dict
    except Exception as e:
        print(f"Error loading themes from database: {e}")
        return None
    finally:
        db.close()


def get_theme_weights_from_db(theme_name: str) -> Optional[Dict[str, float]]:
    """Get scoring weights for a specific theme from database."""
    db = SessionLocal()
    try:
        theme = db.query(ThemeTable).filter(
            ThemeTable.name == theme_name,
            ThemeTable.is_active == "true"
        ).first()
        if not theme:
            return None
        
        return {
            "country_match_weight": theme.country_match_weight,
            "region_match_weight": theme.region_match_weight,
            "sector_match_weight": theme.sector_match_weight,
            "exposure_bonus_weight": theme.exposure_bonus_weight,
            "emerging_market_bonus": theme.emerging_market_bonus,
            "min_relevance_threshold": theme.min_relevance_threshold,
        }
    except Exception as e:
        print(f"Error loading theme weights from database: {e}")
        return None
    finally:
        db.close()
