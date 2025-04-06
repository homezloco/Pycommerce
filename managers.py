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
from models import (
    Tenant, Product, Cart, CartItem, User,
    InventoryRecord, InventoryTransaction
)
# Import these separately to prevent circular imports
from models import Order, OrderItem, Shipment, ShipmentItem

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


class ShipmentManager:
    """Manager for shipment operations."""
    
    def create_shipment(
        self,
        order_id: str,
        shipping_method: str,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        shipping_address: Optional[Dict[str, Any]] = None,
        tracking_url: Optional[str] = None,
        label_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Shipment:
        """Create a new shipment for an order."""
        try:
            # Check if the order exists
            order = Order.query.filter_by(id=order_id).first()
            if not order:
                raise ValueError(f"Order not found: {order_id}")
                
            shipment = Shipment(
                id=str(uuid.uuid4()),
                order_id=order_id,
                status="pending",
                shipping_method=shipping_method,
                tracking_number=tracking_number,
                carrier=carrier,
                shipping_address=shipping_address or {},
                tracking_url=tracking_url,
                label_url=label_url,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(shipment)
            db.session.commit()
            logger.info(f"Created shipment for order {order_id}")
            
            # Update order status if appropriate
            if order.status == "paid":
                order.status = "processing"
                order.updated_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Updated order {order_id} status to processing")
            
            return shipment
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating shipment: {e}")
            raise
    
    def get_shipment_by_id(self, shipment_id: str) -> Optional[Shipment]:
        """Get a shipment by ID."""
        return Shipment.query.filter_by(id=shipment_id).first()
    
    def get_shipments_by_order(self, order_id: str) -> List[Shipment]:
        """Get all shipments for an order."""
        return Shipment.query.filter_by(order_id=order_id).all()
    
    def add_item_to_shipment(
        self,
        shipment_id: str,
        order_item_id: str,
        product_id: str,
        quantity: int
    ) -> ShipmentItem:
        """Add an item to a shipment."""
        try:
            shipment_item = ShipmentItem(
                id=str(uuid.uuid4()),
                shipment_id=shipment_id,
                order_item_id=order_item_id,
                product_id=product_id,
                quantity=quantity,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(shipment_item)
            db.session.commit()
            logger.info(f"Added item to shipment {shipment_id}")
            return shipment_item
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding item to shipment: {e}")
            raise
    
    def update_shipment_status(
        self,
        shipment_id: str,
        status: str,
        tracking_number: Optional[str] = None,
        tracking_url: Optional[str] = None
    ) -> Optional[Shipment]:
        """Update a shipment's status."""
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return None
        
        try:
            # Update status and tracking info
            shipment.status = status
            if tracking_number:
                shipment.tracking_number = tracking_number
            if tracking_url:
                shipment.tracking_url = tracking_url
            
            # Update timestamps based on status
            if status == "shipped":
                shipment.shipped_at = datetime.utcnow()
            elif status == "delivered":
                shipment.delivered_at = datetime.utcnow()
            
            shipment.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Update order status based on shipment status
            order = Order.query.filter_by(id=shipment.order_id).first()
            if order:
                if status == "shipped" and order.status != "shipped":
                    order.status = "shipped"
                    order.updated_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Updated order {order.id} status to shipped")
                elif status == "delivered" and order.status != "delivered":
                    order.status = "delivered"
                    order.updated_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Updated order {order.id} status to delivered")
            
            logger.info(f"Updated shipment {shipment_id} status to {status}")
            return shipment
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating shipment status: {e}")
            raise
    
    def delete_shipment(self, shipment_id: str) -> bool:
        """Delete a shipment."""
        try:
            shipment = self.get_shipment_by_id(shipment_id)
            if not shipment:
                return False
            
            # First delete all shipment items
            ShipmentItem.query.filter_by(shipment_id=shipment_id).delete()
            
            # Then delete the shipment
            db.session.delete(shipment)
            db.session.commit()
            logger.info(f"Deleted shipment {shipment_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting shipment: {e}")
            raise


class InventoryManager:
    """Manager for inventory operations."""
    
    def create_or_update_inventory(
        self,
        product_id: str,
        tenant_id: str,
        quantity: int,
        location: Optional[str] = None,
        sku: Optional[str] = None,
        reorder_point: Optional[int] = None,
        reorder_quantity: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InventoryRecord:
        """Create or update an inventory record for a product."""
        try:
            # Check if inventory record already exists
            inventory = InventoryRecord.query.filter_by(
                product_id=product_id,
                tenant_id=tenant_id
            ).first()
            
            if inventory:
                # Update existing record
                old_quantity = inventory.quantity
                inventory.quantity = quantity
                inventory.available_quantity = quantity - inventory.reserved_quantity
                
                if location is not None:
                    inventory.location = location
                if sku is not None:
                    inventory.sku = sku
                if reorder_point is not None:
                    inventory.reorder_point = reorder_point
                if reorder_quantity is not None:
                    inventory.reorder_quantity = reorder_quantity
                
                # Update metadata if provided
                if metadata:
                    current_metadata = inventory.inventory_metadata or {}
                    current_metadata.update(metadata)
                    inventory.inventory_metadata = current_metadata
                
                inventory.updated_at = datetime.utcnow()
                
                # Create a transaction record for the update
                if quantity != old_quantity:
                    transaction = InventoryTransaction(
                        id=str(uuid.uuid4()),
                        inventory_record_id=inventory.id,
                        transaction_type="adjustment",
                        quantity=quantity - old_quantity,  # Can be positive or negative
                        notes=f"Adjusted quantity from {old_quantity} to {quantity}",
                        created_at=datetime.utcnow()
                    )
                    db.session.add(transaction)
            else:
                # Create new inventory record
                inventory = InventoryRecord(
                    id=str(uuid.uuid4()),
                    product_id=product_id,
                    tenant_id=tenant_id,
                    location=location,
                    sku=sku,
                    quantity=quantity,
                    available_quantity=quantity,
                    reserved_quantity=0,
                    reorder_point=reorder_point or 0,
                    reorder_quantity=reorder_quantity or 0,
                    inventory_metadata=metadata or {},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(inventory)
                
                # Create initial transaction record
                transaction = InventoryTransaction(
                    id=str(uuid.uuid4()),
                    inventory_record_id=inventory.id,
                    transaction_type="initial",
                    quantity=quantity,
                    notes="Initial inventory setup",
                    created_at=datetime.utcnow()
                )
                db.session.add(transaction)
            
            # Update corresponding product stock
            product = Product.query.filter_by(id=product_id).first()
            if product:
                product.stock = quantity
                product.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Created/updated inventory for product {product_id} with quantity {quantity}")
            return inventory
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating/updating inventory: {e}")
            raise
    
    def get_inventory_by_product(self, product_id: str) -> Optional[InventoryRecord]:
        """Get inventory by product ID."""
        return InventoryRecord.query.filter_by(product_id=product_id).first()
    
    def get_inventory_by_sku(self, sku: str, tenant_id: str) -> Optional[InventoryRecord]:
        """Get inventory by SKU and tenant ID."""
        return InventoryRecord.query.filter_by(sku=sku, tenant_id=tenant_id).first()
    
    def reserve_inventory(
        self,
        product_id: str,
        quantity: int,
        reference_id: str,
        reference_type: str = "order"
    ) -> bool:
        """Reserve inventory for an order."""
        try:
            inventory = self.get_inventory_by_product(product_id)
            if not inventory:
                logger.warning(f"No inventory found for product {product_id}")
                return False
            
            if inventory.available_quantity < quantity:
                logger.warning(f"Insufficient inventory for product {product_id}. Requested: {quantity}, Available: {inventory.available_quantity}")
                return False
            
            # Update inventory quantities
            inventory.reserved_quantity += quantity
            inventory.available_quantity -= quantity
            inventory.updated_at = datetime.utcnow()
            
            # Create a transaction record
            transaction = InventoryTransaction(
                id=str(uuid.uuid4()),
                inventory_record_id=inventory.id,
                transaction_type="sale",
                quantity=-quantity,  # Negative because it's a reservation/reduction
                reference_id=reference_id,
                reference_type=reference_type,
                notes=f"Reserved {quantity} units for {reference_type} {reference_id}",
                created_at=datetime.utcnow()
            )
            db.session.add(transaction)
            
            db.session.commit()
            logger.info(f"Reserved {quantity} units of product {product_id} for {reference_type} {reference_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error reserving inventory: {e}")
            raise
    
    def complete_inventory_sale(
        self,
        product_id: str,
        quantity: int,
        reference_id: str,
        reference_type: str = "order"
    ) -> bool:
        """Complete a sale, removing reserved inventory."""
        try:
            inventory = self.get_inventory_by_product(product_id)
            if not inventory:
                logger.warning(f"No inventory found for product {product_id}")
                return False
            
            # Update inventory quantities
            inventory.reserved_quantity = max(0, inventory.reserved_quantity - quantity)
            inventory.updated_at = datetime.utcnow()
            
            # Don't change available_quantity since it was already reduced when reserving
            
            # Create a transaction record
            transaction = InventoryTransaction(
                id=str(uuid.uuid4()),
                inventory_record_id=inventory.id,
                transaction_type="sale",
                quantity=0,  # No change in total quantity, just converting reserved to sold
                reference_id=reference_id,
                reference_type=f"{reference_type}_completion",
                notes=f"Completed sale of {quantity} units for {reference_type} {reference_id}",
                created_at=datetime.utcnow()
            )
            db.session.add(transaction)
            
            # Update product stock
            product = Product.query.filter_by(id=product_id).first()
            if product:
                product.stock = inventory.quantity
            
            db.session.commit()
            logger.info(f"Completed sale of {quantity} units of product {product_id} for {reference_type} {reference_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error completing inventory sale: {e}")
            raise
    
    def process_return(
        self,
        product_id: str,
        quantity: int,
        reference_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Process a product return, adding inventory back."""
        try:
            inventory = self.get_inventory_by_product(product_id)
            if not inventory:
                logger.warning(f"No inventory found for product {product_id}")
                return False
            
            # Update inventory quantities
            inventory.quantity += quantity
            inventory.available_quantity += quantity
            inventory.updated_at = datetime.utcnow()
            
            # Create a transaction record
            transaction = InventoryTransaction(
                id=str(uuid.uuid4()),
                inventory_record_id=inventory.id,
                transaction_type="return",
                quantity=quantity,  # Positive because it's an addition
                reference_id=reference_id,
                reference_type="return",
                notes=notes or f"Return of {quantity} units, reference: {reference_id}",
                created_at=datetime.utcnow()
            )
            db.session.add(transaction)
            
            # Update product stock
            product = Product.query.filter_by(id=product_id).first()
            if product:
                product.stock = inventory.quantity
            
            db.session.commit()
            logger.info(f"Processed return of {quantity} units of product {product_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing return: {e}")
            raise
    
    def get_low_stock_items(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get items that are at or below their reorder point."""
        try:
            # Find inventory records where quantity is at or below reorder point
            low_stock_records = InventoryRecord.query.filter(
                InventoryRecord.tenant_id == tenant_id,
                InventoryRecord.quantity <= InventoryRecord.reorder_point,
                InventoryRecord.reorder_point > 0  # Only include items with a reorder point set
            ).all()
            
            result = []
            for record in low_stock_records:
                product = Product.query.filter_by(id=record.product_id).first()
                if product:
                    result.append({
                        "inventory_id": record.id,
                        "product_id": record.product_id,
                        "product_name": product.name,
                        "sku": record.sku or product.sku,
                        "quantity": record.quantity,
                        "reorder_point": record.reorder_point,
                        "reorder_quantity": record.reorder_quantity,
                        "location": record.location
                    })
            
            return result
        except Exception as e:
            logger.error(f"Error getting low stock items: {e}")
            return []
    
    def get_inventory_transactions(
        self,
        product_id: str,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[InventoryTransaction]:
        """Get inventory transactions for a product."""
        try:
            inventory = self.get_inventory_by_product(product_id)
            if not inventory:
                return []
            
            # Build query
            query = InventoryTransaction.query.filter_by(inventory_record_id=inventory.id)
            
            if transaction_type:
                query = query.filter_by(transaction_type=transaction_type)
            
            if start_date:
                query = query.filter(InventoryTransaction.created_at >= start_date)
            
            if end_date:
                query = query.filter(InventoryTransaction.created_at <= end_date)
            
            return query.order_by(InventoryTransaction.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting inventory transactions: {e}")
            return []