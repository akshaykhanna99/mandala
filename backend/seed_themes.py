"""Seed default themes into the database."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    exit(1)

# Convert postgresql:// to postgresql+psycopg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

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

def seed_themes():
    """Seed default themes into database."""
    db = SessionLocal()
    try:
        import sys
        from pathlib import Path
        # Add project root to path
        project_root = Path(__file__).resolve().parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from backend.db_models import ThemeTable
        from datetime import datetime
        
        for theme_data in default_themes:
            # Check if theme already exists
            existing = db.query(ThemeTable).filter(ThemeTable.name == theme_data['name']).first()
            if existing:
                print(f"⏭️  Theme '{theme_data['name']}' already exists, skipping")
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
            print(f"✅ Added theme: {theme_data['display_name']}")
        
        db.commit()
        print("✅ Themes seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding themes: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_themes()
