"""Add order_type column to orders table

Revision ID: 20250408_add_order_type
Revises: 
Create Date: 2025-04-08 23:01:46.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250408_add_order_type'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create OrderType enum if it doesn't exist
    # We need to first check if the enum exists in the database
    conn = op.get_bind()
    res = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ordertype')"
    ))
    exists = res.scalar()
    
    if not exists:
        # Create the enum type if it doesn't exist
        op.execute("CREATE TYPE ordertype AS ENUM ('STANDARD', 'TEST', 'SUBSCRIPTION', 'WHOLESALE', 'BACKORDER', 'PREORDER', 'GIFT', 'EXPEDITED', 'INTERNATIONAL')")
    
    # Add order_type column to orders table
    op.add_column('orders', sa.Column('order_type', postgresql.ENUM('STANDARD', 'TEST', 'SUBSCRIPTION', 'WHOLESALE', 'BACKORDER', 'PREORDER', 'GIFT', 'EXPEDITED', 'INTERNATIONAL', name='ordertype'), nullable=True))
    
    # Set default values for existing rows
    op.execute("UPDATE orders SET order_type = 'STANDARD' WHERE order_type IS NULL")


def downgrade() -> None:
    # Remove order_type column
    op.drop_column('orders', 'order_type')
    
    # Note: We don't drop the enum type because it might be used elsewhere
    # If you want to drop it, uncomment the line below
    # op.execute("DROP TYPE IF EXISTS ordertype")