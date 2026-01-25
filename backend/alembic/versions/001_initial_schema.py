"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create source_refs table
    op.create_table(
        'source_refs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_refs_id'), 'source_refs', ['id'], unique=False)

    # Create country_snapshots table
    op.create_table(
        'country_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('activity_level', sa.String(), nullable=False),
        sa.Column('updated_at', sa.String(), nullable=False),
        sa.Column('events', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('stats', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at_db', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_country_snapshots_id'), 'country_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_country_snapshots_name'), 'country_snapshots', ['name'], unique=False)

    # Create global_items table
    op.create_table(
        'global_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('source', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('published_at', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('countries', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('country_ids', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_global_items_id'), 'global_items', ['id'], unique=False)
    op.create_index(op.f('ix_global_items_topic'), 'global_items', ['topic'], unique=False)
    op.create_index(op.f('ix_global_items_url'), 'global_items', ['url'], unique=True)

    # Create market_items table
    op.create_table(
        'market_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('change', sa.Float(), nullable=True),
        sa.Column('change_pct', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at_db', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )
    op.create_index(op.f('ix_market_items_id'), 'market_items', ['id'], unique=False)
    op.create_index(op.f('ix_market_items_symbol'), 'market_items', ['symbol'], unique=True)
    op.create_index(op.f('ix_market_items_category'), 'market_items', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_market_items_category'), table_name='market_items')
    op.drop_index(op.f('ix_market_items_symbol'), table_name='market_items')
    op.drop_index(op.f('ix_market_items_id'), table_name='market_items')
    op.drop_table('market_items')
    op.drop_index(op.f('ix_global_items_url'), table_name='global_items')
    op.drop_index(op.f('ix_global_items_topic'), table_name='global_items')
    op.drop_index(op.f('ix_global_items_id'), table_name='global_items')
    op.drop_table('global_items')
    op.drop_index(op.f('ix_country_snapshots_name'), table_name='country_snapshots')
    op.drop_index(op.f('ix_country_snapshots_id'), table_name='country_snapshots')
    op.drop_table('country_snapshots')
    op.drop_index(op.f('ix_source_refs_id'), table_name='source_refs')
    op.drop_table('source_refs')
