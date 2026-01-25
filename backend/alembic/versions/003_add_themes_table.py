"""Add themes table for customizable geopolitical themes

Revision ID: 003
Revises: 002
Create Date: 2025-01-24

Creates themes table to allow users to customize theme definitions and scoring weights.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if themes table already exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'themes' not in tables:
        # Create themes table
        op.create_table(
            'themes',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('display_name', sa.String(), nullable=False),
            sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('relevant_countries', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'),
            sa.Column('relevant_regions', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'),
            sa.Column('relevant_sectors', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('country_match_weight', sa.Float(), nullable=False, server_default='0.4'),
            sa.Column('region_match_weight', sa.Float(), nullable=False, server_default='0.2'),
            sa.Column('sector_match_weight', sa.Float(), nullable=False, server_default='0.3'),
            sa.Column('exposure_bonus_weight', sa.Float(), nullable=False, server_default='0.3'),
            sa.Column('emerging_market_bonus', sa.Float(), nullable=False, server_default='0.1'),
            sa.Column('min_relevance_threshold', sa.Float(), nullable=False, server_default='0.1'),
            sa.Column('is_active', sa.String(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Check and create indexes if they don't exist (whether table was just created or already existed)
    indexes = [idx['name'] for idx in inspector.get_indexes('themes')] if 'themes' in tables else []
    
    if 'ix_themes_name' not in indexes:
        try:
            op.create_index('ix_themes_name', 'themes', ['name'], unique=True)
        except Exception:
            pass  # Index might already exist
    
    if 'ix_themes_is_active' not in indexes:
        try:
            op.create_index('ix_themes_is_active', 'themes', ['is_active'])
        except Exception:
            pass  # Index might already exist
    
    # Insert default themes
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
    
    # Insert default themes
    # Note: We'll insert these via a Python script after migration, or use raw SQL
    # For now, themes will be empty and can be populated via API or manually
    pass


def downgrade() -> None:
    op.drop_index('ix_themes_is_active', table_name='themes')
    op.drop_index('ix_themes_name', table_name='themes')
    op.drop_table('themes')
