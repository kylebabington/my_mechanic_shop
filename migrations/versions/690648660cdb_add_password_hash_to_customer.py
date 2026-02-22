"""add password_hash to customer

Revision ID: 690648660cdb
Revises: 7113897da969
Create Date: 2026-02-17 17:34:26.616276

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '690648660cdb'
down_revision = '7113897da969'
branch_labels = None
depends_on = None


def upgrade():
    # password_hash is already created in baseline (7113897da969); no-op to keep revision chain valid.
    pass


def downgrade():
    pass
