
"""
Inventory-related models and management.

This module defines the InventoryRecord model and InventoryManager class
for managing product inventory in the PyCommerce SDK.
"""

import logging
import uuid
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum

from pycommerce.core.db import Base, engine, get_session
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean, Integer, Text
from sqlalchemy.orm import relationship, Session

logger = logging.getLogger("pycommerce.models.inventory")


class InventoryTransactionType(str, Enum):
    """
    Types of inventory transactions.
    """
    INITIAL = "initial"          # Initial inventory setup
    PURCHASE = "purchase"        # Inventory purchased from supplier
    SALE = "sale"                # Inventory sold to customer
    ADJUSTMENT = "adjustment"    # Manual inventory adjustment
    RETURN = "return"            # Customer return
    DAMAGED = "damaged"          # Inventory damaged or lost
    TRANSFER = "transfer"        # Inventory transferred between locations


# Import InventoryRecord from the registry instead of redefining it
from pycommerce.models.db_registry import InventoryRecord


class InventoryTransaction(Base):
    """
    Represents a transaction affecting inventory.
    """
    __tablename__ = "inventory_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inventory_record_id = Column(String(36), ForeignKey("inventory_records.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)  # Positive for additions, negative for reductions
    reference_id = Column(String(100), nullable=True)  # Optional reference (order ID, etc.)
    reference_type = Column(String(50), nullable=True)  # Type of reference (order, shipment, etc.)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)  # User who created the transaction
    metadata = Column(JSON, nullable=True)

    # Relationships
    inventory_record = relationship("InventoryRecord", back_populates="transactions")

    def __repr__(self):
        return f"<InventoryTransaction {self.id} of type {self.transaction_type}>"


class InventoryManager:
    """
    Manager for inventory operations.
    """

    def __init__(self, session_factory=get_session):
        """
        Initialize the inventory manager.

        Args:
            session_factory: Function that provides a database session
        """
        self.session_factory = session_factory

    def get_inventory(self, product_id: str, location: Optional[str] = None) -> Optional[InventoryRecord]:
        """
        Get the inventory record for a product.

        Args:
            product_id: The ID of the product
            location: Optional location to filter by

        Returns:
            The inventory record, or None if not found
        """
        with self.session_factory() as session:
            query = session.query(InventoryRecord).filter_by(product_id=product_id)
            if location:
                query = query.filter_by(location=location)
            return query.first()

    def get_inventory_by_sku(self, sku: str, tenant_id: str, location: Optional[str] = None) -> Optional[InventoryRecord]:
        """
        Get the inventory record for a product by SKU.

        Args:
            sku: The product SKU
            tenant_id: The tenant ID
            location: Optional location to filter by

        Returns:
            The inventory record, or None if not found
        """
        with self.session_factory() as session:
            query = session.query(InventoryRecord).filter_by(sku=sku, tenant_id=tenant_id)
            if location:
                query = query.filter_by(location=location)
            return query.first()

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
        """
        Create or update an inventory record for a product.

        Args:
            product_id: The ID of the product
            tenant_id: The tenant ID
            quantity: The total quantity
            location: Optional inventory location
            sku: Optional product SKU
            reorder_point: Optional reorder point
            reorder_quantity: Optional reorder quantity
            metadata: Optional additional metadata

        Returns:
            The created or updated inventory record
        """
        with self.session_factory() as session:
            # Check if the product exists
            from pycommerce.models.product import Product
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                raise ValueError(f"Product not found: {product_id}")

            # Get or create the inventory record
            inventory = session.query(InventoryRecord).filter_by(
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

                # Create a transaction for the update if quantity changed
                if quantity != old_quantity:
                    transaction = InventoryTransaction(
                        inventory_record_id=inventory.id,
                        transaction_type=InventoryTransactionType.ADJUSTMENT.value,
                        quantity=quantity - old_quantity,
                        notes=f"Inventory adjustment from {old_quantity} to {quantity}"
                    )
                    session.add(transaction)

            else:
                # Create new record
                inventory = InventoryRecord(
                    product_id=product_id,
                    tenant_id=tenant_id,
                    location=location,
                    sku=sku or product.sku,
                    quantity=quantity,
                    available_quantity=quantity,
                    reserved_quantity=0,
                    reorder_point=reorder_point or 0,
                    reorder_quantity=reorder_quantity or 0,
                    inventory_metadata=metadata or {}
                )
                session.add(inventory)

                # Create an initial transaction
                transaction = InventoryTransaction(
                    inventory_record_id=inventory.id,
                    transaction_type=InventoryTransactionType.INITIAL.value,
                    quantity=quantity,
                    notes=f"Initial inventory setup with quantity {quantity}"
                )
                session.add(transaction)

            session.commit()
            session.refresh(inventory)

            logger.info(f"Created/updated inventory for product {product_id} with quantity {quantity}")

            return inventory

    def reserve_inventory(
        self,
        product_id: str,
        quantity: int,
        reference_id: str,
        reference_type: str = "order",
        location: Optional[str] = None
    ) -> bool:
        """
        Reserve inventory for an order or other purpose.

        Args:
            product_id: The ID of the product
            quantity: The quantity to reserve
            reference_id: The reference ID (e.g., order ID)
            reference_type: The reference type (e.g., 'order')
            location: Optional inventory location

        Returns:
            True if inventory was successfully reserved, False otherwise

        Raises:
            ValueError: If there is insufficient inventory
        """
        with self.session_factory() as session:
            query = session.query(InventoryRecord).filter_by(product_id=product_id)
            if location:
                query = query.filter_by(location=location)

            inventory = query.first()
            if not inventory:
                logger.warning(f"No inventory record found for product {product_id}")
                return False

            if inventory.available_quantity < quantity:
                raise ValueError(f"Insufficient inventory for product {product_id}: requested {quantity}, available {inventory.available_quantity}")

            # Update inventory quantities
            inventory.reserved_quantity += quantity
            inventory.available_quantity -= quantity

            # Create a transaction
            transaction = InventoryTransaction(
                inventory_record_id=inventory.id,
                transaction_type=InventoryTransactionType.SALE.value,
                quantity=-quantity,  # Negative because it's a reduction
                reference_id=reference_id,
                reference_type=reference_type,
                notes=f"Reserved {quantity} units for {reference_type} {reference_id}"
            )
            session.add(transaction)

            session.commit()
            logger.info(f"Reserved {quantity} units of product {product_id} for {reference_type} {reference_id}")

            return True

    def release_inventory(
        self,
        product_id: str,
        quantity: int,
        reference_id: str,
        reference_type: str = "order",
        location: Optional[str] = None
    ) -> bool:
        """
        Release previously reserved inventory.

        Args:
            product_id: The ID of the product
            quantity: The quantity to release
            reference_id: The reference ID (e.g., order ID)
            reference_type: The reference type (e.g., 'order')
            location: Optional inventory location

        Returns:
            True if inventory was successfully released, False otherwise
        """
        with self.session_factory() as session:
            query = session.query(InventoryRecord).filter_by(product_id=product_id)
            if location:
                query = query.filter_by(location=location)

            inventory = query.first()
            if not inventory:
                logger.warning(f"No inventory record found for product {product_id}")
                return False

            # Update inventory quantities
            inventory.reserved_quantity = max(0, inventory.reserved_quantity - quantity)
            inventory.available_quantity = inventory.quantity - inventory.reserved_quantity

            # Create a transaction
            transaction = InventoryTransaction(
                inventory_record_id=inventory.id,
                transaction_type=InventoryTransactionType.ADJUSTMENT.value,
                quantity=quantity,  # Positive because we're releasing (adding back)
                reference_id=reference_id,
                reference_type=reference_type,
                notes=f"Released {quantity} units from {reference_type} {reference_id}"
            )
            session.add(transaction)

            session.commit()
            logger.info(f"Released {quantity} units of product {product_id} from {reference_type} {reference_id}")

            return True

    def complete_order_inventory(
        self,
        order_id: str,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Complete the inventory transaction for an order.
        This converts reserved inventory to consumed inventory.

        Args:
            order_id: The order ID
            items: List of items with product_id and quantity

        Returns:
            List of results for each item

        Raises:
            ValueError: If there is an issue with any item
        """
        results = []

        with self.session_factory() as session:
            for item in items:
                product_id = item["product_id"]
                quantity = item["quantity"]

                inventory = session.query(InventoryRecord).filter_by(product_id=product_id).first()
                if not inventory:
                    error_msg = f"No inventory record found for product {product_id}"
                    logger.warning(error_msg)
                    results.append({
                        "product_id": product_id,
                        "success": False,
                        "message": error_msg
                    })
                    continue

                # Reduce the reserved quantity (it's already taken from available)
                inventory.reserved_quantity = max(0, inventory.reserved_quantity - quantity)

                # Create a transaction to track the completed order
                transaction = InventoryTransaction(
                    inventory_record_id=inventory.id,
                    transaction_type=InventoryTransactionType.SALE.value,
                    quantity=-quantity,  # Negative because it's a final reduction
                    reference_id=order_id,
                    reference_type="order_completion",
                    notes=f"Completed order {order_id} with {quantity} units"
                )
                session.add(transaction)

                results.append({
                    "product_id": product_id,
                    "success": True,
                    "message": f"Successfully processed {quantity} units"
                })

                # Check if we need to reorder
                if inventory.quantity <= inventory.reorder_point:
                    logger.info(f"Product {product_id} has reached reorder point: {inventory.quantity} <= {inventory.reorder_point}")
                    # TODO: Trigger reorder notification or process

            session.commit()
            logger.info(f"Completed inventory processing for order {order_id}")

        return results

    def process_return(
        self,
        product_id: str,
        quantity: int,
        reference_id: str,
        reference_type: str = "return",
        notes: Optional[str] = None,
        location: Optional[str] = None
    ) -> bool:
        """
        Process a product return, adding inventory back.

        Args:
            product_id: The ID of the product
            quantity: The quantity returned
            reference_id: The reference ID (e.g., return ID)
            reference_type: The reference type
            notes: Optional notes about the return
            location: Optional inventory location

        Returns:
            True if return was successfully processed, False otherwise
        """
        with self.session_factory() as session:
            query = session.query(InventoryRecord).filter_by(product_id=product_id)
            if location:
                query = query.filter_by(location=location)

            inventory = query.first()
            if not inventory:
                logger.warning(f"No inventory record found for product {product_id}")
                return False

            # Update inventory quantities
            inventory.quantity += quantity
            inventory.available_quantity += quantity

            # Create a transaction
            transaction = InventoryTransaction(
                inventory_record_id=inventory.id,
                transaction_type=InventoryTransactionType.RETURN.value,
                quantity=quantity,  # Positive because it's an addition
                reference_id=reference_id,
                reference_type=reference_type,
                notes=notes or f"Returned {quantity} units via {reference_type} {reference_id}"
            )
            session.add(transaction)

            session.commit()
            logger.info(f"Processed return of {quantity} units of product {product_id}")

            return True

    def get_low_stock_products(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get products that are at or below their reorder point.

        Args:
            tenant_id: The tenant ID

        Returns:
            List of products with low stock
        """
        with self.session_factory() as session:
            records = session.query(InventoryRecord).filter(
                InventoryRecord.tenant_id == tenant_id,
                InventoryRecord.quantity <= InventoryRecord.reorder_point,
                InventoryRecord.reorder_point > 0  # Only include items with a reorder point set
            ).all()

            result = []
            for record in records:
                # Get the product details
                from pycommerce.models.product import Product
                product = session.query(Product).filter_by(id=record.product_id).first()
                if product:
                    result.append({
                        "product_id": record.product_id,
                        "product_name": product.name if hasattr(product, 'name') else "Unknown",
                        "sku": record.sku or (product.sku if hasattr(product, 'sku') else "Unknown"),
                        "quantity": record.quantity,
                        "reorder_point": record.reorder_point,
                        "reorder_quantity": record.reorder_quantity,
                        "location": record.location
                    })

            return result

    def get_inventory_transactions(
        self,
        product_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None
    ) -> List[InventoryTransaction]:
        """
        Get inventory transactions for a product.

        Args:
            product_id: The ID of the product
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            transaction_type: Optional transaction type to filter by

        Returns:
            List of inventory transactions
        """
        with self.session_factory() as session:
            # First get the inventory record
            inventory = session.query(InventoryRecord).filter_by(product_id=product_id).first()
            if not inventory:
                return []

            # Query transactions
            query = session.query(InventoryTransaction).filter_by(inventory_record_id=inventory.id)

            if start_date:
                query = query.filter(InventoryTransaction.created_at >= start_date)
            if end_date:
                query = query.filter(InventoryTransaction.created_at <= end_date)
            if transaction_type:
                query = query.filter(InventoryTransaction.transaction_type == transaction_type)

            return query.order_by(InventoryTransaction.created_at.desc()).all()


# Create the tables
Base.metadata.create_all(engine)
