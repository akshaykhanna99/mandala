"""Add assets and gp_scans tables for saving scan results

Revision ID: 005
Revises: 004
Create Date: 2025-01-24

Creates assets and gp_scans tables to store asset information and GP risk scan results.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assets table
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('ticker', sa.String(), nullable=True),
        sa.Column('isin', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=False),
        sa.Column('sub_region', sa.String(), nullable=True),
        sa.Column('asset_type', sa.String(), nullable=False),
        sa.Column('asset_class', sa.String(), nullable=False),
        sa.Column('sector', sa.String(), nullable=False),
        sa.Column('is_emerging_market', sa.String(), nullable=False, server_default='false'),
        sa.Column('is_developed_market', sa.String(), nullable=False, server_default='false'),
        sa.Column('is_global_fund', sa.String(), nullable=False, server_default='false'),
        sa.Column('exposures', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for assets
    op.create_index('ix_assets_name', 'assets', ['name'])
    op.create_index('ix_assets_ticker', 'assets', ['ticker'])
    op.create_index('ix_assets_isin', 'assets', ['isin'])
    op.create_index('ix_assets_country', 'assets', ['country'])
    op.create_index('ix_assets_sector', 'assets', ['sector'])
    
    # Create gp_scans table
    op.create_table(
        'gp_scans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('risk_tolerance', sa.String(), nullable=False),
        sa.Column('days_lookback', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('scan_date', sa.DateTime(), nullable=False),
        sa.Column('pipeline_result', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('negative_probability', sa.Float(), nullable=False),
        sa.Column('neutral_probability', sa.Float(), nullable=False),
        sa.Column('positive_probability', sa.Float(), nullable=False),
        sa.Column('overall_direction', sa.String(), nullable=False),
        sa.Column('overall_magnitude', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('signal_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('top_themes', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for gp_scans
    op.create_index('ix_gp_scans_asset_id', 'gp_scans', ['asset_id'])
    op.create_index('ix_gp_scans_scan_date', 'gp_scans', ['scan_date'])


def downgrade() -> None:
    op.drop_index('ix_gp_scans_scan_date', table_name='gp_scans')
    op.drop_index('ix_gp_scans_asset_id', table_name='gp_scans')
    op.drop_table('gp_scans')
    op.drop_index('ix_assets_sector', table_name='assets')
    op.drop_index('ix_assets_country', table_name='assets')
    op.drop_index('ix_assets_isin', table_name='assets')
    op.drop_index('ix_assets_ticker', table_name='assets')
    op.drop_index('ix_assets_name', table_name='assets')
    op.drop_table('assets')
