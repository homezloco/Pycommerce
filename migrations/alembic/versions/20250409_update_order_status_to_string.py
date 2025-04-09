"""Update order status to string

Revision ID: 20250409_order_status_string
Revises: 20250408_add_order_type_column
Create Date: 2025-04-09 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250409_order_status_string'
down_revision = '20250408_add_order_type'
branch_labels = None
depends_on = None


def upgrade():
    # We need to convert the status column from ENUM to String
    # First, create a new status_str column
    op.add_column('orders', sa.Column('status_str', sa.String(50), nullable=True))
    
    # Copy data from status ENUM to status_str (using an SQL script)
    op.execute("""
        UPDATE orders
        SET status_str = status::text
    """)
    
    # Make the new column non-nullable
    op.alter_column('orders', 'status_str', nullable=False)
    
    # Drop the old status column
    op.drop_column('orders', 'status')
    
    # Rename status_str to status
    op.alter_column('orders', 'status_str', new_column_name='status')


def downgrade():
    # Create the ENUM type if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'orderstatus') THEN
                CREATE TYPE orderstatus AS ENUM (
                    'PENDING', 'PROCESSING', 'PAID', 'SHIPPED', 
                    'DELIVERED', 'COMPLETED', 'CANCELLED', 'REFUNDED'
                );
            END IF;
        END
        $$;
    """)
    
    # Create a temporary status_enum column
    op.add_column('orders', sa.Column('status_enum', postgresql.ENUM('PENDING', 'PROCESSING', 'PAID', 'SHIPPED', 
                                                                    'DELIVERED', 'COMPLETED', 'CANCELLED', 'REFUNDED', 
                                                                    name='orderstatus'), nullable=True))
    
    # Copy data from status string to status_enum
    op.execute("""
        UPDATE orders
        SET status_enum = status::orderstatus
    """)
    
    # Drop the string status column
    op.drop_column('orders', 'status')
    
    # Rename status_enum to status
    op.alter_column('orders', 'status_enum', new_column_name='status')
    
    # Make the column non-nullable with default
    op.alter_column('orders', 'status', nullable=False, server_default="PENDING")