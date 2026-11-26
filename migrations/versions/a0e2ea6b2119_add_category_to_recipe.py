"""Add category to Recipe

Revision ID: a0e2ea6b2119
Revises: eb7f1675a04f
Create Date: 2026-10-26 20:49:54.546492

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0e2ea6b2119'
down_revision = 'eb7f1675a04f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'recipe_id',
            name='uq_user_recipe_favorite'
        )
    )


def downgrade():
    op.drop_table('favorites')
