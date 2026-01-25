"""Add indexes for intelligence retrieval optimization

Revision ID: 002
Revises: 001
Create Date: 2025-01-24

Adds database indexes to optimize intelligence retrieval queries:
- GIN index on global_items.countries (array search)
- Index on global_items.published_at (date filtering)
- Index on country_snapshots.activity_level (priority filtering)
- Index on country_snapshots.updated_at_db (date filtering)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on global_items.published_at for date filtering
    # Note: published_at is a String, so we'll create a functional index
    # For better performance, we could add a computed column, but keeping it simple for now
    op.create_index(
        'ix_global_items_published_at',
        'global_items',
        ['published_at'],
        unique=False
    )
    
    # Add GIN index on global_items.countries array for array containment queries
    # This allows efficient queries like: WHERE 'Turkey' = ANY(countries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_global_items_countries_gin 
        ON global_items USING GIN(countries);
    """)
    
    # Add index on country_snapshots.activity_level for priority filtering
    op.create_index(
        'ix_country_snapshots_activity_level',
        'country_snapshots',
        ['activity_level'],
        unique=False
    )
    
    # Add index on country_snapshots.updated_at_db for date filtering
    op.create_index(
        'ix_country_snapshots_updated_at_db',
        'country_snapshots',
        ['updated_at_db'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_country_snapshots_updated_at_db', table_name='country_snapshots')
    op.drop_index('ix_country_snapshots_activity_level', table_name='country_snapshots')
    op.execute("DROP INDEX IF EXISTS ix_global_items_countries_gin;")
    op.drop_index('ix_global_items_published_at', table_name='global_items')
