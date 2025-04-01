"""
Managers for the Flask application.

This module provides manager classes to handle the application logic.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from app import db
from models import Tenant, Product, Cart, CartItem, Order, OrderItem, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenantManager:
    """Manager for tenant operations."""
    
    def create_tenant(self, name: str, slug: str, domain: Optional[str] = None) -> Tenant:
        """Create a new tenant."""
        try:
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name=name,
                slug=slug,
                domain=domain,
                active=True,
                settings={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(tenant)
            db.session.commit()
            logger.info(f"Created tenant: {name} ({slug})")
            return tenant
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating tenant: {e}")
            raise
    
    def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get a tenant by ID."""
        return Tenant.query.filter_by(id=tenant_id).first()
    
    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get a tenant by slug."""
        return Tenant.query.filter_by(slug=slug).first()
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get a tenant by domain."""
        return Tenant.query.filter_by(domain=domain).first()
    
    def get_all_tenants(self) -> List[Tenant]:
        """Get all tenants."""
        return Tenant.query.all()
    
    def update_tenant(self, tenant_id: str, **kwargs) -> Optional[Tenant]:
        """Update a tenant."""
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None
        
        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.utcnow()
        db.session.commit()
        return tenant
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant."""
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return False
        
        db.session.delete(tenant)
        db.session.commit()
        return True

class ProductManager:
    """Manager for product operations."""
    
    def create_product(
        self, 
        tenant_id: str, 
        name: str, 
        description: Optional[str] = None,
        price: float = 0.0,
        sku: str = "",
        stock: int = 0,
        categories: List[str] = None,
        active: bool = True
    ) -> Product:
        """Create a new product."""
        try:
            if categories is None:
                categories = []
                
            product = Product(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name=name,
                description=description,
                price=price,
                sku=sku,
                stock=stock,
                categories=categories,
                active=active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(product)
            db.session.commit()
            logger.info(f"Created product: {name} for tenant {tenant_id}")
            return product
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating product: {e}")
            raise
    
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Get a product by ID."""
        return Product.query.filter_by(id=product_id).first()
    
    def get_products_by_tenant(self, tenant_id: str, filters: Dict[str, Any] = None) -> List[Product]:
        """Get products for a tenant with optional filtering."""
        if filters is None:
            filters = {}
            
        query = Product.query.filter_by(tenant_id=tenant_id)
        
        # Apply filters
        if "category" in filters:
            # Filter by category (JSON field contains the category)
            category = filters["category"]
            # This is a simplification - in a real app, you'd use a proper JSON query
            query = query.filter(Product.categories.contains(f'["{category}"]'))
        
        if "min_price" in filters:
            query = query.filter(Product.price >= filters["min_price"])
        
        if "max_price" in filters:
            query = query.filter(Product.price <= filters["max_price"])
        
        if "in_stock" in filters and filters["in_stock"]:
            query = query.filter(Product.stock > 0)
        
        return query.all()
    
    def update_product(self, product_id: str, **kwargs) -> Optional[Product]:
        """Update a product."""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        return product
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product."""
        product = self.get_product_by_id(product_id)
        if not product:
            return False
        
        db.session.delete(product)
        db.session.commit()
        return True

class CartManager:
    """Manager for cart operations."""
    
    def create_cart(self, tenant_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Cart:
        """Create a new cart."""
        try:
            cart = Cart(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(cart)
            db.session.commit()
            logger.info(f"Created cart for tenant {tenant_id}")
            return cart
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating cart: {e}")
            raise
    
    def get_cart_by_id(self, cart_id: str) -> Optional[Cart]:
        """Get a cart by ID."""
        return Cart.query.filter_by(id=cart_id).first()
    
    def get_cart_by_session(self, session_id: str) -> Optional[Cart]:
        """Get a cart by session ID."""
        return Cart.query.filter_by(session_id=session_id).first()
    
    def get_cart_by_user(self, user_id: str) -> Optional[Cart]:
        """Get a cart by user ID."""
        return Cart.query.filter_by(user_id=user_id).first()
    
    def add_item_to_cart(self, cart_id: str, product_id: str, quantity: int = 1) -> CartItem:
        """Add an item to a cart."""
        try:
            # Check if item already exists in cart
            cart_item = CartItem.query.filter_by(cart_id=cart_id, product_id=product_id).first()
            
            if cart_item:
                # Update quantity
                cart_item.quantity += quantity
                cart_item.updated_at = datetime.utcnow()
            else:
                # Create new item
                cart_item = CartItem(
                    id=str(uuid.uuid4()),
                    cart_id=cart_id,
                    product_id=product_id,
                    quantity=quantity,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(cart_item)
            
            db.session.commit()
            logger.info(f"Added/updated item {product_id} in cart {cart_id}")
            return cart_item
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding item to cart: {e}")
            raise
    
    def update_cart_item(self, cart_id: str, product_id: str, quantity: int) -> Optional[CartItem]:
        """Update a cart item quantity."""
        try:
            cart_item = CartItem.query.filter_by(cart_id=cart_id, product_id=product_id).first()
            if not cart_item:
                return None
            
            if quantity <= 0:
                # Remove item if quantity is zero or negative
                db.session.delete(cart_item)
            else:
                # Update quantity
                cart_item.quantity = quantity
                cart_item.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Updated item {product_id} in cart {cart_id}")
            return cart_item if quantity > 0 else None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating cart item: {e}")
            raise
    
    def remove_item_from_cart(self, cart_id: str, product_id: str) -> bool:
        """Remove an item from a cart."""
        try:
            cart_item = CartItem.query.filter_by(cart_id=cart_id, product_id=product_id).first()
            if not cart_item:
                return False
            
            db.session.delete(cart_item)
            db.session.commit()
            logger.info(f"Removed item {product_id} from cart {cart_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing item from cart: {e}")
            raise
    
    def clear_cart(self, cart_id: str) -> bool:
        """Clear all items from a cart."""
        try:
            CartItem.query.filter_by(cart_id=cart_id).delete()
            db.session.commit()
            logger.info(f"Cleared all items from cart {cart_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error clearing cart: {e}")
            raise
    
    def delete_cart(self, cart_id: str) -> bool:
        """Delete a cart."""
        try:
            cart = self.get_cart_by_id(cart_id)
            if not cart:
                return False
            
            # First delete all cart items
            CartItem.query.filter_by(cart_id=cart_id).delete()
            
            # Then delete the cart
            db.session.delete(cart)
            db.session.commit()
            logger.info(f"Deleted cart {cart_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting cart: {e}")
            raise

class OrderManager:
    """Manager for order operations."""
    
    def create_order(
        self,
        tenant_id: str,
        email: str,
        user_id: Optional[str] = None,
        shipping_address: Dict[str, Any] = None,
        billing_address: Dict[str, Any] = None,
        payment_info: Dict[str, Any] = None,
        shipping_method: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> Order:
        """Create a new order."""
        try:
            if shipping_address is None:
                shipping_address = {}
            
            if billing_address is None:
                billing_address = {}
            
            if payment_info is None:
                payment_info = {}
            
            order = Order(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                status="pending",
                total=0.0,
                email=email,
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_info=payment_info,
                shipping_method=shipping_method,
                payment_method=payment_method,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(order)
            db.session.commit()
            logger.info(f"Created order for tenant {tenant_id}")
            return order
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating order: {e}")
            raise
    
    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get an order by ID."""
        return Order.query.filter_by(id=order_id).first()
    
    def get_orders_by_tenant(self, tenant_id: str) -> List[Order]:
        """Get all orders for a tenant."""
        return Order.query.filter_by(tenant_id=tenant_id).all()
    
    def get_orders_by_user(self, user_id: str) -> List[Order]:
        """Get all orders for a user."""
        return Order.query.filter_by(user_id=user_id).all()
    
    def add_item_to_order(self, order_id: str, product_id: str, quantity: int, price: float) -> OrderItem:
        """Add an item to an order."""
        try:
            order_item = OrderItem(
                id=str(uuid.uuid4()),
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                price=price,
                created_at=datetime.utcnow()
            )
            db.session.add(order_item)
            
            # Update order total
            order = self.get_order_by_id(order_id)
            if order:
                order.total += price * quantity
                order.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Added item {product_id} to order {order_id}")
            return order_item
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding item to order: {e}")
            raise
    
    def update_order(self, order_id: str, **kwargs) -> Optional[Order]:
        """Update an order."""
        order = self.get_order_by_id(order_id)
        if not order:
            return None
        
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        return order
    
    def delete_order(self, order_id: str) -> bool:
        """Delete an order."""
        try:
            order = self.get_order_by_id(order_id)
            if not order:
                return False
            
            # First delete all order items
            OrderItem.query.filter_by(order_id=order_id).delete()
            
            # Then delete the order
            db.session.delete(order)
            db.session.commit()
            logger.info(f"Deleted order {order_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting order: {e}")
            raise

class UserManager:
    """Manager for user operations."""
    
    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Create a new user."""
        try:
            user = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created user: {username}")
            return user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return User.query.filter_by(id=user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return User.query.filter_by(username=username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return User.query.filter_by(email=email).first()
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        db.session.delete(user)
        db.session.commit()
        return True