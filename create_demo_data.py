import os
import sys
import logging
import uuid
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Flask app and models
from app import app, db
from models import Tenant, Product

def create_tenant(name, slug, domain=None):
    """Create a tenant with settings."""
    # Check if tenant already exists
    existing = Tenant.query.filter_by(slug=slug).first()
    if existing:
        logger.info(f"Tenant '{name}' already exists with slug '{slug}'")
        return existing
    
    # Create new tenant
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        domain=domain,
        active=True,
        settings={
            'primary_color': '#3498db',
            'secondary_color': '#6c757d',
            'background_color': '#ffffff',
            'text_color': '#212529',
            'font_family': 'Arial, sans-serif',
            'logo_position': 'left'
        }
    )
    
    db.session.add(tenant)
    db.session.commit()
    logger.info(f"Created tenant: {name} (slug: {slug})")
    return tenant

def create_product(tenant_id, name, price, description, sku, stock, categories=None):
    """Create a product."""
    # Check if product already exists
    existing = Product.query.filter_by(tenant_id=tenant_id, sku=sku).first()
    if existing:
        logger.info(f"Product '{name}' already exists with SKU '{sku}'")
        return existing
    
    # Create product
    product = Product(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=name,
        description=description,
        price=price,
        sku=sku,
        stock=stock,
        categories=categories or []
    )
    
    db.session.add(product)
    db.session.commit()
    logger.info(f"Created product: {name} (SKU: {sku})")
    return product

def create_demo_data():
    """Create demo tenants and products."""
    with app.app_context():
        # Create tenants
        tech_store = create_tenant("Tech Gadgets", "tech", "tech.example.com")
        outdoor_store = create_tenant("Outdoor Adventure", "outdoor", "outdoor.example.com")
        fashion_store = create_tenant("Fashion Boutique", "fashion", "fashion.example.com")
        
        # Tech store products
        create_product(
            tech_store.id,
            "Premium Laptop",
            1299.99,
            "High-performance laptop with 16GB RAM and 512GB SSD",
            "TECH-001",
            25,
            ["Laptops", "Electronics"]
        )
        
        create_product(
            tech_store.id,
            "Wireless Headphones",
            199.99,
            "Noise-cancelling wireless headphones with 30-hour battery life",
            "TECH-002",
            50,
            ["Audio", "Accessories"]
        )
        
        create_product(
            tech_store.id,
            "Smartphone Pro",
            899.99,
            "Latest smartphone with triple camera and 5G connectivity",
            "TECH-003",
            30,
            ["Phones", "Electronics"]
        )
        
        create_product(
            tech_store.id,
            "Smart Watch",
            249.99,
            "Fitness tracking and notifications with 7-day battery life",
            "TECH-004",
            40,
            ["Wearables", "Accessories"]
        )
        
        create_product(
            tech_store.id,
            "Wireless Earbuds",
            149.99,
            "True wireless earbuds with charging case and water resistance",
            "TECH-005",
            60,
            ["Audio", "Accessories"]
        )
        
        # Outdoor store products
        create_product(
            outdoor_store.id,
            "Hiking Backpack",
            129.99,
            "65L hiking backpack with internal frame and rain cover",
            "OUT-001",
            20,
            ["Hiking", "Bags"]
        )
        
        create_product(
            outdoor_store.id,
            "Camping Tent",
            199.99,
            "4-person waterproof tent with easy setup",
            "OUT-002",
            15,
            ["Camping", "Shelters"]
        )
        
        create_product(
            outdoor_store.id,
            "Trekking Poles",
            49.99,
            "Adjustable aluminum trekking poles with cork grips",
            "OUT-003",
            30,
            ["Hiking", "Accessories"]
        )
        
        create_product(
            outdoor_store.id,
            "Sleeping Bag",
            89.99,
            "3-season sleeping bag rated for 20°F",
            "OUT-004",
            25,
            ["Camping", "Sleep Gear"]
        )
        
        create_product(
            outdoor_store.id,
            "Water Filter",
            39.99,
            "Portable water filter that removes 99.9% of bacteria",
            "OUT-005",
            40,
            ["Camping", "Hydration"]
        )
        
        # Fashion store products
        create_product(
            fashion_store.id,
            "Men's Slim Jeans",
            59.99,
            "Slim fit jeans in dark wash with stretch comfort",
            "FASH-001",
            40,
            ["Men's", "Bottoms"]
        )
        
        create_product(
            fashion_store.id,
            "Women's Casual Dress",
            79.99,
            "Floral print casual dress with short sleeves",
            "FASH-002",
            35,
            ["Women's", "Dresses"]
        )
        
        create_product(
            fashion_store.id,
            "Unisex Sneakers",
            89.99,
            "Classic canvas sneakers in multiple colors",
            "FASH-003",
            50,
            ["Footwear", "Casual"]
        )
        
        create_product(
            fashion_store.id,
            "Leather Tote Bag",
            119.99,
            "Genuine leather tote with multiple compartments",
            "FASH-004",
            20,
            ["Accessories", "Bags"]
        )
        
        create_product(
            fashion_store.id,
            "Wool Scarf",
            39.99,
            "Soft wool blend scarf in plaid pattern",
            "FASH-005",
            30,
            ["Accessories", "Winter"]
        )
        
        logger.info("Demo data creation complete!")

if __name__ == "__main__":
    create_demo_data()