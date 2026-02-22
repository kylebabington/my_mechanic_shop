"""baseline

Revision ID: 7113897da969
Revises: 
Create Date: 2026-02-17 17:33:11.554998

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7113897da969'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create base tables for empty database (customers, mechanics, service_tickets, service_mechanics).
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "mechanics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("salary", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "service_tickets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("VIN", sa.String(length=50), nullable=False),
        sa.Column("service_date", sa.String(length=50), nullable=False),
        sa.Column("service_desc", sa.String(length=255), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "service_mechanics",
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("mechanic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["mechanic_id"], ["mechanics.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["service_tickets.id"]),
        sa.PrimaryKeyConstraint("ticket_id", "mechanic_id"),
    )


def downgrade():
    op.drop_table("service_mechanics")
    op.drop_table("service_tickets")
    op.drop_table("mechanics")
    op.drop_table("customers")
