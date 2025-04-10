#!/usr/bin/env python
"""List all tenants in the database."""

import sys
from app import app, db
from models import Tenant, Order

with app.app_context():
    print("Available tenants:")
    tenants = Tenant.query.all()
    for tenant in tenants:
        print(f"ID: {tenant.id}, Name: {tenant.name}, Slug: {tenant.slug}")
        
    print("\nChecking orders...")
    for tenant in tenants:
        orders = Order.query.filter_by(tenant_id=tenant.id).all()
        print(f"Tenant '{tenant.name}' has {len(orders)} orders.")