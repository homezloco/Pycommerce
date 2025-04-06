import os
import sys
import logging
import uuid
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import SQLAlchemy models and db
from database import db
from models import Tenant, Product
from app import app

def create_sample_tenant(name, slug, domain=None):
    """Create a sample tenant with theme configuration."""
    session = next(get_session())
    
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
        theme_settings={
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
    session = next(get_session())
    
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
    session = next(get_session())
    
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
        image_url=image_url,
        categories=categories or []
    )
    
    session.add(product)
    session.commit()
    logger.info(f"Created product: {name} (SKU: {sku}) for tenant {tenant_id}")
    return product

def create_sample_data():
    """Create sample tenants and products."""
    # Create tenants
    outdoor_store = create_sample_tenant(
        "Outdoor Adventure", 
        "outdoor", 
        "outdoor.example.com"
    )
    
    tech_store = create_sample_tenant(
        "Tech Gadgets", 
        "tech", 
        "tech.example.com"
    )
    
    fashion_store = create_sample_tenant(
        "Fashion Boutique", 
        "fashion", 
        "fashion.example.com"
    )
    
    # Create categories for Outdoor Adventure
    hiking = create_category(outdoor_store.id, "Hiking")
    camping = create_category(outdoor_store.id, "Camping")
    climbing = create_category(outdoor_store.id, "Climbing")
    
    # Create products for Outdoor Adventure
    create_product(
        outdoor_store.id,
        "Hiking Boots",
        129.99,
        "Waterproof hiking boots with excellent ankle support and grip for all terrains.",
        "OUT-HB-001",
        50,
        [hiking.name],
        "/static/images/hiking-boots.jpg"
    )
    
    create_product(
        outdoor_store.id,
        "Backpack 40L",
        79.99,
        "Durable 40-liter backpack with multiple compartments and hydration compatibility.",
        "OUT-BP-001",
        75,
        [hiking.name, camping.name],
        "/static/images/backpack.jpg"
    )
    
    create_product(
        outdoor_store.id,
        "Tent 2-Person",
        199.99,
        "Lightweight 2-person tent, easy to set up and packs down small.",
        "OUT-TN-001",
        30,
        [camping.name],
        "/static/images/tent.jpg"
    )
    
    create_product(
        outdoor_store.id,
        "Climbing Rope 60m",
        159.99,
        "Dynamic climbing rope, 60 meters with high durability and safety features.",
        "OUT-CR-001",
        20,
        [climbing.name],
        "/static/images/climbing-rope.jpg"
    )
    
    create_product(
        outdoor_store.id,
        "GPS Navigator",
        249.99,
        "Rugged GPS device with preloaded maps and long battery life.",
        "OUT-GPS-001",
        15,
        [hiking.name, camping.name],
        "/static/images/gps-navigator.jpg"
    )
    
    # Create categories for Tech Gadgets
    laptops = create_category(tech_store.id, "Laptops")
    smartphones = create_category(tech_store.id, "Smartphones")
    accessories = create_category(tech_store.id, "Accessories")
    
    # Create products for Tech Gadgets
    create_product(
        tech_store.id,
        "Ultrabook Pro",
        1299.99,
        "Thin and light laptop with 16GB RAM, 512GB SSD, and 14-inch 4K display.",
        "TECH-LT-001",
        25,
        [laptops.name],
        "/static/images/laptop.jpg"
    )
    
    create_product(
        tech_store.id,
        "Smartphone X",
        899.99,
        "Latest smartphone with 6.7-inch OLED display, 128GB storage, and triple camera system.",
        "TECH-SP-001",
        40,
        [smartphones.name],
        "/static/images/smartphone.jpg"
    )
    
    create_product(
        tech_store.id,
        "Wireless Earbuds",
        149.99,
        "True wireless earbuds with noise cancellation and 24-hour battery life.",
        "TECH-ACC-001",
        100,
        [accessories.name],
        "/static/images/earbuds.jpg"
    )
    
    create_product(
        tech_store.id,
        "Smart Watch",
        299.99,
        "Smart watch with health tracking, GPS, and 5-day battery life.",
        "TECH-ACC-002",
        50,
        [accessories.name],
        "/static/images/smartwatch.jpg"
    )
    
    create_product(
        tech_store.id,
        "4K Monitor 27\"",
        349.99,
        "27-inch 4K monitor with HDR support and USB-C connectivity.",
        "TECH-ACC-003",
        20,
        [accessories.name],
        "/static/images/monitor.jpg"
    )
    
    # Create categories for Fashion Boutique
    mens = create_category(fashion_store.id, "Men's Clothing")
    womens = create_category(fashion_store.id, "Women's Clothing")
    accessories_f = create_category(fashion_store.id, "Accessories")
    
    # Create products for Fashion Boutique
    create_product(
        fashion_store.id,
        "Men's Slim Fit Jeans",
        79.99,
        "Slim fit jeans in dark wash denim with stretch for comfort.",
        "FASH-M-001",
        80,
        [mens.name],
        "/static/images/mens-jeans.jpg"
    )
    
    create_product(
        fashion_store.id,
        "Women's Midi Dress",
        89.99,
        "Floral print midi dress with short sleeves and button front.",
        "FASH-W-001",
        65,
        [womens.name],
        "/static/images/womens-dress.jpg"
    )
    
    create_product(
        fashion_store.id,
        "Leather Belt",
        45.99,
        "Genuine leather belt with classic buckle.",
        "FASH-A-001",
        100,
        [accessories_f.name, mens.name],
        "/static/images/belt.jpg"
    )
    
    create_product(
        fashion_store.id,
        "Women's Sunglasses",
        59.99,
        "Oversized sunglasses with UV protection and tortoise shell frames.",
        "FASH-A-002",
        70,
        [accessories_f.name, womens.name],
        "/static/images/sunglasses.jpg"
    )
    
    create_product(
        fashion_store.id,
        "Men's Oxford Shirt",
        69.99,
        "Classic Oxford button-down shirt in light blue cotton.",
        "FASH-M-002",
        60,
        [mens.name],
        "/static/images/oxford-shirt.jpg"
    )
    
    logger.info("Sample data generation complete")

if __name__ == "__main__":
    create_sample_data()