
# PyCommerce Project Structure

## Core Application Files

- `main.py` - Main application entry point with WSGI adapter
- `web_app.py` - FastAPI application configuration
- `asgi_wsgi_app.py` - ASGI/WSGI bridge for deployment

## Directory Structure

```
pycommerce/
├── pycommerce/           # Core SDK and business logic
│   ├── api/             # API routes and schemas
│   ├── core/            # Database, config, plugins
│   ├── models/          # SQLAlchemy models
│   ├── plugins/         # Payment, shipping, AI plugins
│   ├── services/        # Business logic services
│   └── utils/           # Utility functions
├── routes/              # Web application routes
│   ├── admin/           # Admin interface routes
│   ├── api/             # REST API endpoints
│   └── storefront/      # Customer-facing routes
├── templates/           # Jinja2 templates
│   ├── admin/           # Admin interface templates
│   ├── storefront/      # Customer templates
│   └── emails/          # Email templates
├── static/              # Static assets (CSS, JS, images)
├── scripts/             # Utility and maintenance scripts
├── docs/                # Documentation
├── migrations/          # Database migrations
└── data/                # Application data
```

## Key Configuration Files

- `requirements.txt` - Python dependencies
- `package.json` - Frontend dependencies
- `alembic.ini` - Database migration configuration
- `.replit` - Replit configuration
- `.gitignore` - Git ignore rules

## Scripts

All utility scripts have been moved to the `scripts/` directory and organized by purpose. See `scripts/README.md` for details.
