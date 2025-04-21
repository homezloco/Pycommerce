"""
Estimate service for PyCommerce.

This module provides functionality for managing estimates, including creating,
retrieving, updating, and converting estimates to orders.
"""

import logging
import uuid
import random
import string
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from pycommerce.core.db import get_session
from pycommerce.models.estimate import Estimate, EstimateMaterial, EstimateLabor
from pycommerce.models.order import Order
from pycommerce.models.order_item import OrderItem

logger = logging.getLogger(__name__)


class EstimateService:
    """Service class for estimates."""
    
    def __init__(self):
        """Initialize the EstimateService."""
        from pycommerce.models.order import OrderManager
        self.order_manager = OrderManager()
    
    def generate_estimate_number(self) -> str:
        """Generate a unique estimate number."""
        # Generate a random string of 8 characters
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(8))
        
        # Add a timestamp prefix to ensure uniqueness
        timestamp_part = datetime.now().strftime("%y%m%d")
        
        return f"EST-{timestamp_part}-{random_part}"
    
    def get_by_id(self, estimate_id: str) -> Optional[Estimate]:
        """
        Get an estimate by ID.
        
        Args:
            estimate_id: The ID of the estimate
            
        Returns:
            The estimate if found, None otherwise
        """
        try:
            with get_session() as session:
                return session.query(Estimate).filter(Estimate.id == estimate_id).first()
        except Exception as e:
            logger.error(f"Error getting estimate: {str(e)}")
            return None
    
    def get_for_tenant(self, tenant_id: str) -> List[Estimate]:
        """
        Get all estimates for a tenant.
        
        Args:
            tenant_id: The ID of the tenant
            
        Returns:
            List of estimates
        """
        try:
            with get_session() as session:
                return session.query(Estimate)\
                    .filter(Estimate.tenant_id == tenant_id)\
                    .order_by(Estimate.created_at.desc())\
                    .all()
        except Exception as e:
            logger.error(f"Error getting estimates: {str(e)}")
            return []
    
    def create_estimate(self, data: Dict[str, Any]) -> Optional[Estimate]:
        """
        Create a new estimate.
        
        Args:
            data: Dictionary containing estimate data with optional 'materials' and 'labor_items' lists
            
        Returns:
            The created estimate if successful, None otherwise
        """
        try:
            with get_session() as session:
                # Generate estimate number if not provided
                if 'estimate_number' not in data or not data['estimate_number']:
                    data['estimate_number'] = self.generate_estimate_number()
                
                # Extract materials and labor items if present
                materials_data = data.pop('materials', [])
                labor_data = data.pop('labor_items', [])
                
                # Create the estimate
                estimate = Estimate(**data)
                session.add(estimate)
                session.flush()  # Flush to get the ID
                
                # Add materials
                for material_data in materials_data:
                    material_data['estimate_id'] = estimate.id
                    material = EstimateMaterial(**material_data)
                    session.add(material)
                
                # Add labor items
                for labor_item_data in labor_data:
                    labor_item_data['estimate_id'] = estimate.id
                    labor = EstimateLabor(**labor_item_data)
                    session.add(labor)
                
                # Calculate totals
                estimate.calculate_totals()
                
                session.commit()
                session.refresh(estimate)
                return estimate
        except Exception as e:
            logger.error(f"Error creating estimate: {str(e)}")
            return None
    
    def update_estimate(self, estimate_id: str, data: Dict[str, Any]) -> Optional[Estimate]:
        """
        Update an estimate.
        
        Args:
            estimate_id: The ID of the estimate to update
            data: Dictionary containing updated estimate data with optional 'materials' and 'labor_items' lists
            
        Returns:
            The updated estimate if successful, None otherwise
        """
        try:
            with get_session() as session:
                estimate = session.query(Estimate).filter(Estimate.id == estimate_id).first()
                if not estimate:
                    return None
                
                # Extract materials and labor items if present
                materials_data = data.pop('materials', None)
                labor_data = data.pop('labor_items', None)
                
                # Update estimate attributes
                for key, value in data.items():
                    if hasattr(estimate, key) and key != 'id':
                        setattr(estimate, key, value)
                
                # Update materials if provided
                if materials_data is not None:
                    # Remove existing materials
                    session.query(EstimateMaterial).filter(EstimateMaterial.estimate_id == estimate_id).delete()
                    
                    # Add new materials
                    for material_data in materials_data:
                        material_data['estimate_id'] = estimate.id
                        material = EstimateMaterial(**material_data)
                        session.add(material)
                
                # Update labor items if provided
                if labor_data is not None:
                    # Remove existing labor items
                    session.query(EstimateLabor).filter(EstimateLabor.estimate_id == estimate_id).delete()
                    
                    # Add new labor items
                    for labor_item_data in labor_data:
                        labor_item_data['estimate_id'] = estimate.id
                        labor = EstimateLabor(**labor_item_data)
                        session.add(labor)
                
                # Recalculate totals
                estimate.calculate_totals()
                
                session.commit()
                session.refresh(estimate)
                return estimate
        except Exception as e:
            logger.error(f"Error updating estimate: {str(e)}")
            return None
    
    def delete_estimate(self, estimate_id: str) -> bool:
        """
        Delete an estimate.
        
        Args:
            estimate_id: The ID of the estimate to delete
            
        Returns:
            True if the estimate was deleted successfully, False otherwise
        """
        try:
            with get_session() as session:
                estimate = session.query(Estimate).filter(Estimate.id == estimate_id).first()
                if not estimate:
                    return False
                
                session.delete(estimate)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting estimate: {str(e)}")
            return False
    
    def convert_to_order(self, estimate_id: str) -> Tuple[Optional[Order], Optional[str]]:
        """
        Convert an estimate to an order.
        
        Args:
            estimate_id: The ID of the estimate to convert
            
        Returns:
            Tuple containing (created order, error message)
            If successful, the first element will be the order and the second will be None
            If unsuccessful, the first element will be None and the second will be an error message
        """
        try:
            with get_session() as session:
                estimate = session.query(Estimate).filter(Estimate.id == estimate_id).first()
                if not estimate:
                    return None, "Estimate not found"
                
                # Create order data from estimate
                order_data = {
                    'tenant_id': estimate.tenant_id,
                    'customer_id': estimate.customer_id,
                    'customer_email': estimate.customer_email,
                    'customer_name': estimate.customer_name,
                    'customer_phone': estimate.customer_phone,
                    'subtotal': estimate.subtotal,
                    'tax': estimate.tax,
                    'total': estimate.total,
                    'total_cost': estimate.total_cost,
                    'materials_cost': sum(m.cost_price * m.quantity for m in estimate.materials),
                    'labor_cost': sum(l.cost_price * l.hours for l in estimate.labor_items),
                    'profit': estimate.total_profit,
                    'profit_margin': estimate.profit_margin,
                    'estimate_id': estimate.id  # Link back to the original estimate
                }
                
                # Create the order
                order = self.order_manager.create_order(order_data)
                if not order:
                    return None, "Failed to create order"
                
                # Add order items from estimate materials
                for material in estimate.materials:
                    order_item_data = {
                        'order_id': order.id,
                        'product_id': material.product_id if material.product_id else str(uuid.uuid4()),
                        'quantity': int(material.quantity),
                        'price': material.selling_price,
                        'cost_price': material.cost_price,
                        'is_material': True,
                        'is_labor': False
                    }
                    
                    order_item = OrderItem(**order_item_data)
                    session.add(order_item)
                
                # Add order items from estimate labor
                for labor_item in estimate.labor_items:
                    order_item_data = {
                        'order_id': order.id,
                        'product_id': str(uuid.uuid4()),  # Generate a unique ID for labor
                        'quantity': 1,
                        'price': labor_item.selling_price * labor_item.hours,
                        'cost_price': labor_item.cost_price * labor_item.hours,
                        'is_material': False,
                        'is_labor': True,
                        'hours': labor_item.hours,
                        'labor_rate': labor_item.selling_price
                    }
                    
                    order_item = OrderItem(**order_item_data)
                    session.add(order_item)
                
                # Update estimate status to "CONVERTED"
                estimate.status = "CONVERTED"
                
                session.commit()
                session.refresh(order)
                return order, None
        except Exception as e:
            error_msg = f"Error converting estimate to order: {str(e)}"
            logger.error(error_msg)
            return None, error_msg