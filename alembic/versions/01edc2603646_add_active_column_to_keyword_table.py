"""Add 'active' column to keyword table

Revision ID: 01edc2603646
Revises: a5beef0a0d51
Create Date: 2022-05-25 14:55:17.747149

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01edc2603646'
down_revision = 'a5beef0a0d51'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('keyword', sa.Column('active', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('keyword', 'active')
    # ### end Alembic commands ###
