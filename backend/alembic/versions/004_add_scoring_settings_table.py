"""Add scoring_settings table for tunable scoring parameters

Revision ID: 004
Revises: 003
Create Date: 2025-01-24

Creates scoring_settings table to allow users to customize all scoring weights, thresholds, and parameters.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scoring_settings table
    op.create_table(
        'scoring_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        
        # Scoring weights
        sa.Column('weight_base_relevance', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('weight_theme_match', sa.Float(), nullable=False, server_default='0.25'),
        sa.Column('weight_recency', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('weight_source_quality', sa.Float(), nullable=False, server_default='0.15'),
        sa.Column('weight_activity_level', sa.Float(), nullable=False, server_default='0.1'),
        
        # Recency decay
        sa.Column('recency_decay_constant', sa.Float(), nullable=False, server_default='30.0'),
        
        # Base relevance scores
        sa.Column('score_country_exact_match', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('score_country_partial_match', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('score_region_match', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('score_sector_match', sa.Float(), nullable=False, server_default='0.2'),
        
        # Activity level scores (JSON)
        sa.Column('activity_level_scores', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        
        # Source quality scores (JSON)
        sa.Column('source_quality_scores', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        
        # Thresholds
        sa.Column('semantic_threshold', sa.Float(), nullable=False, server_default='0.6'),
        sa.Column('relevance_threshold_low', sa.Float(), nullable=False, server_default='0.05'),
        sa.Column('relevance_threshold_high', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('theme_relevance_threshold_web', sa.Float(), nullable=False, server_default='0.3'),
        
        # Pipeline parameters
        sa.Column('days_lookback_default', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('max_signals_default', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('max_events_per_snapshot', sa.Integer(), nullable=False, server_default='3'),
        
        # Semantic filtering
        sa.Column('use_semantic_filtering', sa.String(), nullable=False, server_default='true'),
        
        sa.Column('is_active', sa.String(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_scoring_settings_name', 'scoring_settings', ['name'], unique=True)
    op.create_index('ix_scoring_settings_is_active', 'scoring_settings', ['is_active'])
    
    # Insert default settings
    from datetime import datetime
    
    default_activity_scores = {
        "Critical": 1.0,
        "High": 0.8,
        "Medium": 0.5,
        "Low": 0.2,
        "default": 0.3,
    }
    
    default_source_scores = {
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
    }
    
    # Insert default settings
    # Note: Default settings should be seeded using seed_scoring_settings.py script
    # or via the API after migration completes


def downgrade() -> None:
    op.drop_index('ix_scoring_settings_is_active', table_name='scoring_settings')
    op.drop_index('ix_scoring_settings_name', table_name='scoring_settings')
    op.drop_table('scoring_settings')
