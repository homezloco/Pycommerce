
# Scripts Directory

This directory contains utility scripts for PyCommerce development and maintenance.

## Directory Structure

- **setup/** - Database initialization and setup scripts
- **demo/** - Demo data creation and sample content scripts  
- **debug/** - Debugging and diagnostic utilities
- **migration/** - Database migration scripts

## Usage

Most scripts should be run from the project root directory:

```bash
# Setup database
python scripts/setup/initialize_db.py

# Create demo data
python scripts/demo/create_demo_data.py

# Debug page builder
python scripts/debug/debug_page_builder.py

# Run migrations
python scripts/migration/migrate_categories.py
```

## Important Scripts

### Setup Scripts
- `initialize_db.py` - Initialize database schema
- `add_default_sections.py` - Add default page sections
- `add_page_templates.py` - Add page templates

### Demo Scripts  
- `create_demo_data.py` - Create sample data
- `generate_sample_data.py` - Generate test products/orders
- `dashboard_demo_data.py` - Create dashboard demo data

### Debug Scripts
- `debug_page_builder.py` - Page builder diagnostics
- `debug_database.py` - Database inspection
- `debug_frontend.py` - Frontend template debugging
