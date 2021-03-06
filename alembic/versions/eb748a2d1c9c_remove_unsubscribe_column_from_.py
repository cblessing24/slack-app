"""remove_unsubscribe_column_from_subscription_table

Revision ID: eb748a2d1c9c
Revises: e306363461d7
Create Date: 2022-06-01 11:05:56.954775

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb748a2d1c9c'
down_revision = 'e306363461d7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('subscription', 'unsubscribed')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('subscription', sa.Column('unsubscribed', sa.BOOLEAN(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
