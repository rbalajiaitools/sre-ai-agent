"""add related_knowledge to investigations

Revision ID: add_related_knowledge
Revises: 
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_related_knowledge'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add related_knowledge column to investigations table
    with op.batch_alter_table('investigations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('related_knowledge', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove related_knowledge column from investigations table
    with op.batch_alter_table('investigations', schema=None) as batch_op:
        batch_op.drop_column('related_knowledge')
