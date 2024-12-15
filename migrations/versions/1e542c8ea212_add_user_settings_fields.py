"""Add user settings fields

Revision ID: 1e542c8ea212
Revises: 
Create Date: 2024-12-15 14:53:19.756931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e542c8ea212'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('api_key', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('email_notifications', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('web_notifications', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('web_notifications')
        batch_op.drop_column('email_notifications')
        batch_op.drop_column('api_key')

    # ### end Alembic commands ###
