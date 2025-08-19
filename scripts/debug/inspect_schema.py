"""
Inspect database schema to understand table structure
"""
from app import db, app
import sqlalchemy as sa

def inspect_table(table_name):
    """Inspect a table's columns and structure"""
    with app.app_context():
        inspector = sa.inspect(db.engine)
        
        # Get columns
        print(f"\n{table_name.upper()} TABLE COLUMNS:")
        for column in inspector.get_columns(table_name):
            print(f"  - {column['name']} ({column['type']})")
            
        # Get primary keys
        print(f"\n{table_name.upper()} PRIMARY KEYS:")
        for pk in inspector.get_pk_constraint(table_name)['constrained_columns']:
            print(f"  - {pk}")
            
        # Get foreign keys
        print(f"\n{table_name.upper()} FOREIGN KEYS:")
        for fk in inspector.get_foreign_keys(table_name):
            print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

if __name__ == "__main__":
    # Inspect relevant tables
    inspect_table('orders')
    inspect_table('order_items')
    inspect_table('products')
    inspect_table('categories')