import os
import sys
import logging
import uuid
from uuid import uuid4
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import SQLAlchemy models and db
from database import db
from models import Tenant, Product
from app import app
from initialize_db import ProductCategory

@contextmanager
def get_session():
    """Create a scoped database session."""
    with app.app_context():
        session = db.session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

def create_sample_tenant(name, slug, domain=None):
    """Create a sample tenant with theme configuration."""
    with get_session() as session:
        # Check if tenant already exists
        existing = session.query(Tenant).filter(Tenant.slug == slug).first()
        if existing:
            logger.info(f"Tenant '{name}' already exists with slug '{slug}'")
            return existing
        
        # Create new tenant
        tenant = Tenant(
            id=str(uuid4()),
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
            'heading_font_family': 'inherit',
            'base_font_size': 16,
            'heading_scale': 'moderate',
            'container_width': 'standard',
            'border_radius': 4,
            'spacing_scale': 'moderate',
            'header_style': 'standard',
            'product_card_style': 'standard',
            'button_style': 'standard',
            'custom_css': '',
            'updated_at': datetime.utcnow().isoformat()
        }
    )
    
    session.add(tenant)
    session.commit()
    logger.info(f"Created tenant: {name} (slug: {slug})")
    return tenant

def create_category(tenant_id, name, description=None):
    """Create a product category."""
    with get_session() as session:
        # Check if category already exists
        existing = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == tenant_id,
            ProductCategory.name == name
        ).first()
        
        if existing:
            return existing
        
        category = ProductCategory(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description or f"Products in the {name} category",
            slug=name.lower().replace(' ', '-')
        )
        
        session.add(category)
        session.commit()
        logger.info(f"Created category: {name} for tenant {tenant_id}")
        return category

def create_product(tenant_id, name, price, description, sku, stock, categories=None, image_url=None):
    """Create a product."""
    with get_session() as session:
        # Check if product already exists
        existing = session.query(Product).filter(
            Product.tenant_id == tenant_id,
            Product.sku == sku
        ).first()
        
        if existing:
            return existing
        
        product = Product(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            price=price,
            sku=sku,
            stock=stock,
            categories=categories or []
        )
        
        session.add(product)
        session.commit()
        logger.info(f"Created product: {name} (SKU: {sku}) for tenant {tenant_id}")
        return product

def create_sample_data():
    """Create sample tenants and products."""
    # Create Outdoor Adventure tenant and products
    with get_session() as session:
        # Find or create tenants within the session
        outdoor_tenant = session.query(Tenant).filter(Tenant.slug == "outdoor").first()
        if not outdoor_tenant:
            outdoor_tenant = Tenant(
                id=str(uuid4()),
                name="Outdoor Adventure",
                slug="outdoor",
                domain="outdoor.example.com"
            )
            session.add(outdoor_tenant)
            session.commit()
            logger.info(f"Created tenant: Outdoor Adventure (slug: outdoor)")
        else:
            logger.info(f"Tenant 'Outdoor Adventure' already exists with slug 'outdoor'")
        
        outdoor_id = outdoor_tenant.id
        
        # Create categories for Outdoor Adventure within the same session
        hiking = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == outdoor_id,
            ProductCategory.name == "Hiking"
        ).first()
        
        if not hiking:
            hiking = ProductCategory(
                id=str(uuid4()),
                tenant_id=outdoor_id,
                name="Hiking",
                description="Products for hiking",
                slug="hiking"
            )
            session.add(hiking)
            session.commit()
            logger.info(f"Created category: Hiking for tenant {outdoor_id}")
        
        camping = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == outdoor_id,
            ProductCategory.name == "Camping"
        ).first()
        
        if not camping:
            camping = ProductCategory(
                id=str(uuid4()),
                tenant_id=outdoor_id,
                name="Camping",
                description="Products for camping",
                slug="camping"
            )
            session.add(camping)
            session.commit()
            logger.info(f"Created category: Camping for tenant {outdoor_id}")
        
        climbing = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == outdoor_id,
            ProductCategory.name == "Climbing"
        ).first()
        
        if not climbing:
            climbing = ProductCategory(
                id=str(uuid4()),
                tenant_id=outdoor_id,
                name="Climbing",
                description="Products for climbing",
                slug="climbing"
            )
            session.add(climbing)
            session.commit()
            logger.info(f"Created category: Climbing for tenant {outdoor_id}")
        
        # Create products for Outdoor Adventure
        product = session.query(Product).filter(
            Product.tenant_id == outdoor_id,
            Product.sku == "OUT-HB-001"
        ).first()
        
        if not product:
            product = Product(
                id=str(uuid4()),
                tenant_id=outdoor_id,
                name="Hiking Boots",
                description="Waterproof hiking boots with excellent ankle support and grip for all terrains.",
                price=129.99,
                sku="OUT-HB-001",
                stock=50,
                categories=[hiking.name]
            )
            session.add(product)
            session.commit()
            logger.info(f"Created product: Hiking Boots (SKU: OUT-HB-001) for tenant {outdoor_id}")
        
        product = session.query(Product).filter(
            Product.tenant_id == outdoor_id,
            Product.sku == "OUT-BP-001"
        ).first()
        
        if not product:
            product = Product(
                id=str(uuid4()),
                tenant_id=outdoor_id,
                name="Backpack 40L",
                description="Durable 40-liter backpack with multiple compartments and hydration compatibility.",
                price=79.99,
                sku="OUT-BP-001",
                stock=75,
                categories=[hiking.name, camping.name]
            )
            session.add(product)
            session.commit()
            logger.info(f"Created product: Backpack 40L (SKU: OUT-BP-001) for tenant {outdoor_id}")
        
        product = session.query(Product).filter(
            Product.tenant_id == outdoor_id,
            Product.sku == "OUT-TN-001"
        ).first()
        
        if not product:
            product = Product(
                id=str(uuid4()),
                tenant_id=outdoor_id,
                name="Tent 2-Person",
                description="Lightweight 2-person tent, easy to set up and packs down small.",
                price=199.99,
                sku="OUT-TN-001",
                stock=30,
                categories=[camping.name]
            )
            session.add(product)
            session.commit()
            logger.info(f"Created product: Tent 2-Person (SKU: OUT-TN-001) for tenant {outdoor_id}")
        
        product = session.query(Product).filter(
            Product.tenant_id == outdoor_id,
            Product.sku == "OUT-CR-001"
        ).first()
        
        if not product:
            product = Product(
                id=str(uuid4()),
                tenant_id=outdoor_id,
                name="Climbing Rope 60m",
                description="Dynamic climbing rope, 60 meters with high durability and safety features.",
                price=159.99,
                sku="OUT-CR-001",
                stock=20,
                categories=[climbing.name]
            )
            session.add(product)
            session.commit()
            logger.info(f"Created product: Climbing Rope 60m (SKU: OUT-CR-001) for tenant {outdoor_id}")
        
        product = session.query(Product).filter(
            Product.tenant_id == outdoor_id,
            Product.sku == "OUT-GPS-001"
        ).first()
        
        if not product:
            product = Product(
                id=str(uuid4()),
                tenant_id=outdoor_id,
                name="GPS Navigator",
                description="Rugged GPS device with preloaded maps and long battery life.",
                price=249.99,
                sku="OUT-GPS-001",
                stock=15,
                categories=[hiking.name, camping.name]
            )
            session.add(product)
            session.commit()
            logger.info(f"Created product: GPS Navigator (SKU: OUT-GPS-001) for tenant {outdoor_id}")
    
    # Create Tech Gadgets tenant and products
    with get_session() as session:
        tech_tenant = session.query(Tenant).filter(Tenant.slug == "tech").first()
        if not tech_tenant:
            tech_tenant = Tenant(
                id=str(uuid4()),
                name="Tech Gadgets",
                slug="tech",
                domain="tech.example.com"
            )
            session.add(tech_tenant)
            session.commit()
            logger.info(f"Created tenant: Tech Gadgets (slug: tech)")
        else:
            logger.info(f"Tenant 'Tech Gadgets' already exists with slug 'tech'")
        
        tech_id = tech_tenant.id
        
        # Create categories for Tech Gadgets
        laptops = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == tech_id,
            ProductCategory.name == "Laptops"
        ).first()
        
        if not laptops:
            laptops = ProductCategory(
                id=str(uuid4()),
                tenant_id=tech_id,
                name="Laptops",
                description="Laptop computers",
                slug="laptops"
            )
            session.add(laptops)
            session.commit()
            logger.info(f"Created category: Laptops for tenant {tech_id}")
        
        smartphones = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == tech_id,
            ProductCategory.name == "Smartphones"
        ).first()
        
        if not smartphones:
            smartphones = ProductCategory(
                id=str(uuid4()),
                tenant_id=tech_id,
                name="Smartphones",
                description="Smartphones and mobile devices",
                slug="smartphones"
            )
            session.add(smartphones)
            session.commit()
            logger.info(f"Created category: Smartphones for tenant {tech_id}")
        
        accessories = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == tech_id,
            ProductCategory.name == "Accessories"
        ).first()
        
        if not accessories:
            accessories = ProductCategory(
                id=str(uuid4()),
                tenant_id=tech_id,
                name="Accessories",
                description="Tech accessories and peripherals",
                slug="accessories"
            )
            session.add(accessories)
            session.commit()
            logger.info(f"Created category: Accessories for tenant {tech_id}")
        
        # Create products for Tech Gadgets
        product = session.query(Product).filter(
            Product.tenant_id == tech_id,
            Product.sku == "TECH-LT-001"
        ).first()
        
        if not product:
            product = Product(
                id=str(uuid4()),
                tenant_id=tech_id,
                name="Ultrabook Pro",
                description="Thin and light laptop with 16GB RAM, 512GB SSD, and 14-inch 4K display.",
                price=1299.99,
                sku="TECH-LT-001",
                stock=25,
                categories=[laptops.name]
            )
            session.add(product)
            session.commit()
            logger.info(f"Created product: Ultrabook Pro (SKU: TECH-LT-001) for tenant {tech_id}")
    
    # Create Fashion Boutique tenant and products
    with get_session() as session:
        fashion_tenant = session.query(Tenant).filter(Tenant.slug == "fashion").first()
        if not fashion_tenant:
            fashion_tenant = Tenant(
                id=str(uuid4()),
                name="Fashion Boutique",
                slug="fashion",
                domain="fashion.example.com"
            )
            session.add(fashion_tenant)
            session.commit()
            logger.info(f"Created tenant: Fashion Boutique (slug: fashion)")
        else:
            logger.info(f"Tenant 'Fashion Boutique' already exists with slug 'fashion'")
        
        fashion_id = fashion_tenant.id
        
        # Create categories for Fashion Boutique
        mens = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == fashion_id,
            ProductCategory.name == "Men's Clothing"
        ).first()
        
        if not mens:
            mens = ProductCategory(
                id=str(uuid4()),
                tenant_id=fashion_id,
                name="Men's Clothing",
                description="Clothing for men",
                slug="mens-clothing"
            )
            session.add(mens)
            session.commit()
            logger.info(f"Created category: Men's Clothing for tenant {fashion_id}")
        
        womens = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == fashion_id,
            ProductCategory.name == "Women's Clothing"
        ).first()
        
        if not womens:
            womens = ProductCategory(
                id=str(uuid4()),
                tenant_id=fashion_id,
                name="Women's Clothing",
                description="Clothing for women",
                slug="womens-clothing"
            )
            session.add(womens)
            session.commit()
            logger.info(f"Created category: Women's Clothing for tenant {fashion_id}")
        
        accessories_f = session.query(ProductCategory).filter(
            ProductCategory.tenant_id == fashion_id,
            ProductCategory.name == "Accessories"
        ).first()
        
        if not accessories_f:
            accessories_f = ProductCategory(
                id=str(uuid4()),
                tenant_id=fashion_id,
                name="Accessories",
                description="Fashion accessories",
                slug="accessories"
            )
            session.add(accessories_f)
            session.commit()
            logger.info(f"Created category: Accessories for tenant {fashion_id}")
        
        # Create product for Fashion Boutique
        product = session.query(Product).filter(
            Product.tenant_id == fashion_id,
            Product.sku == "FASH-M-001"
        ).first()
        
        if not product:
            product = Product(
                id=str(uuid4()),
                tenant_id=fashion_id,
                name="Men's Slim Fit Jeans",
                description="Slim fit jeans in dark wash denim with stretch for comfort.",
                price=79.99,
                sku="FASH-M-001",
                stock=80,
                categories=[mens.name]
            )
            session.add(product)
            session.commit()
            logger.info(f"Created product: Men's Slim Fit Jeans (SKU: FASH-M-001) for tenant {fashion_id}")
    
    logger.info("Sample data generation complete")

if __name__ == "__main__":
    create_sample_data()