"""API routes for theme management."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..db_models import ThemeTable
from ..schemas.themes import ThemeCreate, ThemeUpdate, ThemeResponse

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("", response_model=List[ThemeResponse])
def list_themes(active_only: bool = False, db: Session = Depends(get_db)):
    """List all themes, optionally filtered to active only."""
    query = db.query(ThemeTable)
    if active_only:
        query = query.filter(ThemeTable.is_active == "true")
    themes = query.order_by(ThemeTable.name).all()
    
    return [
        ThemeResponse(
            id=theme.id,
            name=theme.name,
            display_name=theme.display_name,
            keywords=theme.keywords or [],
            relevant_countries=theme.relevant_countries or [],
            relevant_regions=theme.relevant_regions or [],
            relevant_sectors=theme.relevant_sectors or [],
            country_match_weight=theme.country_match_weight,
            region_match_weight=theme.region_match_weight,
            sector_match_weight=theme.sector_match_weight,
            exposure_bonus_weight=theme.exposure_bonus_weight,
            emerging_market_bonus=theme.emerging_market_bonus,
            min_relevance_threshold=theme.min_relevance_threshold,
            is_active=theme.is_active == "true",
            created_at=theme.created_at.isoformat() if theme.created_at else "",
            updated_at=theme.updated_at.isoformat() if theme.updated_at else "",
        )
        for theme in themes
    ]


@router.get("/{theme_name}", response_model=ThemeResponse)
def get_theme(theme_name: str, db: Session = Depends(get_db)):
    """Get a specific theme by name."""
    theme = db.query(ThemeTable).filter(ThemeTable.name == theme_name).first()
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_name}' not found")
    
    return ThemeResponse(
        id=theme.id,
        name=theme.name,
        display_name=theme.display_name,
        keywords=theme.keywords or [],
        relevant_countries=theme.relevant_countries or [],
        relevant_regions=theme.relevant_regions or [],
        relevant_sectors=theme.relevant_sectors or [],
        country_match_weight=theme.country_match_weight,
        region_match_weight=theme.region_match_weight,
        sector_match_weight=theme.sector_match_weight,
        exposure_bonus_weight=theme.exposure_bonus_weight,
        emerging_market_bonus=theme.emerging_market_bonus,
        min_relevance_threshold=theme.min_relevance_threshold,
        is_active=theme.is_active == "true",
        created_at=theme.created_at.isoformat() if theme.created_at else "",
        updated_at=theme.updated_at.isoformat() if theme.updated_at else "",
    )


@router.post("", response_model=ThemeResponse, status_code=201)
def create_theme(theme: ThemeCreate, db: Session = Depends(get_db)):
    """Create a new theme."""
    # Check if theme with this name already exists
    existing = db.query(ThemeTable).filter(ThemeTable.name == theme.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Theme '{theme.name}' already exists")
    
    db_theme = ThemeTable(
        name=theme.name,
        display_name=theme.display_name,
        keywords=theme.keywords or [],
        relevant_countries=theme.relevant_countries or [],
        relevant_regions=theme.relevant_regions or [],
        relevant_sectors=theme.relevant_sectors or [],
        country_match_weight=theme.country_match_weight,
        region_match_weight=theme.region_match_weight,
        sector_match_weight=theme.sector_match_weight,
        exposure_bonus_weight=theme.exposure_bonus_weight,
        emerging_market_bonus=theme.emerging_market_bonus,
        min_relevance_threshold=theme.min_relevance_threshold,
        is_active="true" if theme.is_active else "false",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(db_theme)
    db.commit()
    db.refresh(db_theme)
    
    return ThemeResponse(
        id=db_theme.id,
        name=db_theme.name,
        display_name=db_theme.display_name,
        keywords=db_theme.keywords or [],
        relevant_countries=db_theme.relevant_countries or [],
        relevant_regions=db_theme.relevant_regions or [],
        relevant_sectors=db_theme.relevant_sectors or [],
        country_match_weight=db_theme.country_match_weight,
        region_match_weight=db_theme.region_match_weight,
        sector_match_weight=db_theme.sector_match_weight,
        exposure_bonus_weight=db_theme.exposure_bonus_weight,
        emerging_market_bonus=db_theme.emerging_market_bonus,
        min_relevance_threshold=db_theme.min_relevance_threshold,
        is_active=db_theme.is_active == "true",
        created_at=db_theme.created_at.isoformat() if db_theme.created_at else "",
        updated_at=db_theme.updated_at.isoformat() if db_theme.updated_at else "",
    )


@router.put("/{theme_name}", response_model=ThemeResponse)
def update_theme(theme_name: str, theme_update: ThemeUpdate, db: Session = Depends(get_db)):
    """Update an existing theme."""
    theme = db.query(ThemeTable).filter(ThemeTable.name == theme_name).first()
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_name}' not found")
    
    # Update fields if provided
    if theme_update.display_name is not None:
        theme.display_name = theme_update.display_name
    if theme_update.keywords is not None:
        theme.keywords = theme_update.keywords
    if theme_update.relevant_countries is not None:
        theme.relevant_countries = theme_update.relevant_countries
    if theme_update.relevant_regions is not None:
        theme.relevant_regions = theme_update.relevant_regions
    if theme_update.relevant_sectors is not None:
        theme.relevant_sectors = theme_update.relevant_sectors
    if theme_update.country_match_weight is not None:
        theme.country_match_weight = theme_update.country_match_weight
    if theme_update.region_match_weight is not None:
        theme.region_match_weight = theme_update.region_match_weight
    if theme_update.sector_match_weight is not None:
        theme.sector_match_weight = theme_update.sector_match_weight
    if theme_update.exposure_bonus_weight is not None:
        theme.exposure_bonus_weight = theme_update.exposure_bonus_weight
    if theme_update.emerging_market_bonus is not None:
        theme.emerging_market_bonus = theme_update.emerging_market_bonus
    if theme_update.min_relevance_threshold is not None:
        theme.min_relevance_threshold = theme_update.min_relevance_threshold
    if theme_update.is_active is not None:
        theme.is_active = "true" if theme_update.is_active else "false"
    
    theme.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(theme)
    
    return ThemeResponse(
        id=theme.id,
        name=theme.name,
        display_name=theme.display_name,
        keywords=theme.keywords or [],
        relevant_countries=theme.relevant_countries or [],
        relevant_regions=theme.relevant_regions or [],
        relevant_sectors=theme.relevant_sectors or [],
        country_match_weight=theme.country_match_weight,
        region_match_weight=theme.region_match_weight,
        sector_match_weight=theme.sector_match_weight,
        exposure_bonus_weight=theme.exposure_bonus_weight,
        emerging_market_bonus=theme.emerging_market_bonus,
        min_relevance_threshold=theme.min_relevance_threshold,
        is_active=theme.is_active == "true",
        created_at=theme.created_at.isoformat() if theme.created_at else "",
        updated_at=theme.updated_at.isoformat() if theme.updated_at else "",
    )


@router.delete("/{theme_name}", status_code=204)
def delete_theme(theme_name: str, db: Session = Depends(get_db)):
    """Delete a theme (soft delete by setting is_active=false)."""
    theme = db.query(ThemeTable).filter(ThemeTable.name == theme_name).first()
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_name}' not found")
    
    # Soft delete
    theme.is_active = "false"
    theme.updated_at = datetime.utcnow()
    db.commit()
    
    return None


def _seed_default_themes(db: Session):
    """Internal function to seed default themes into the database if they don't exist."""
    default_themes = [
        {
            'name': 'sanctions',
            'display_name': 'Sanctions',
            'keywords': ['sanction', 'embargo', 'trade ban', 'restriction'],
            'relevant_countries': ['Russia', 'Iran', 'North Korea', 'Turkey', 'China'],
            'relevant_sectors': ['Financials', 'Energy', 'Technology', 'Defense'],
        },
        {
            'name': 'trade_disruption',
            'display_name': 'Trade Disruption',
            'keywords': ['trade war', 'tariff', 'export ban', 'import restriction', 'supply chain'],
            'relevant_countries': ['China', 'United States', 'Turkey', 'Russia'],
            'relevant_sectors': ['Technology', 'Manufacturing', 'Energy', 'Agriculture'],
        },
        {
            'name': 'political_instability',
            'display_name': 'Political Instability',
            'keywords': ['coup', 'election', 'protest', 'unrest', 'regime change'],
            'relevant_countries': ['Turkey', 'Thailand', 'Egypt', 'Venezuela', 'Pakistan'],
            'relevant_sectors': ['Financials', 'Infrastructure', 'Government'],
        },
        {
            'name': 'currency_volatility',
            'display_name': 'Currency Volatility',
            'keywords': ['currency', 'inflation', 'devaluation', 'exchange rate', 'monetary policy'],
            'relevant_countries': ['Turkey', 'Argentina', 'Brazil', 'South Africa', 'India'],
            'relevant_sectors': ['Financials', 'Government'],
        },
        {
            'name': 'energy_security',
            'display_name': 'Energy Security',
            'keywords': ['energy', 'oil', 'gas', 'pipeline', 'supply', 'sanction'],
            'relevant_countries': ['Russia', 'Saudi Arabia', 'Iran', 'Turkey', 'Qatar'],
            'relevant_sectors': ['Energy', 'Utilities', 'Infrastructure'],
        },
        {
            'name': 'regional_conflict',
            'display_name': 'Regional Conflict',
            'keywords': ['conflict', 'war', 'military', 'border', 'dispute', 'tension'],
            'relevant_regions': ['Middle East', 'Eastern Europe', 'Asia Pacific', 'Emerging Markets'],
            'relevant_sectors': ['Defense', 'Energy', 'Infrastructure'],
        },
        {
            'name': 'regulatory_changes',
            'display_name': 'Regulatory Changes',
            'keywords': ['regulation', 'policy', 'law', 'compliance', 'government'],
            'relevant_countries': ['China', 'United States', 'European Union'],
            'relevant_sectors': ['Financials', 'Technology', 'Energy', 'Healthcare'],
        },
        {
            'name': 'supply_chain_risk',
            'display_name': 'Supply Chain Risk',
            'keywords': ['supply chain', 'manufacturing', 'logistics', 'trade'],
            'relevant_countries': ['China', 'Vietnam', 'Thailand', 'Mexico'],
            'relevant_sectors': ['Technology', 'Manufacturing', 'Consumer'],
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for theme_data in default_themes:
        # Check if theme already exists
        existing = db.query(ThemeTable).filter(ThemeTable.name == theme_data['name']).first()
        if existing:
            skipped_count += 1
            continue
        
        theme = ThemeTable(
            name=theme_data['name'],
            display_name=theme_data['display_name'],
            keywords=theme_data['keywords'],
            relevant_countries=theme_data.get('relevant_countries', []),
            relevant_regions=theme_data.get('relevant_regions', []),
            relevant_sectors=theme_data['relevant_sectors'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(theme)
        created_count += 1
    
    db.commit()
    
    return {
        "status": "success",
        "created": created_count,
        "skipped": skipped_count,
        "message": f"Seeded {created_count} themes, skipped {skipped_count} existing themes"
    }


@router.post("/seed", status_code=201)
def seed_default_themes(db: Session = Depends(get_db)):
    """Seed default themes into the database if they don't exist."""
    return _seed_default_themes(db)
