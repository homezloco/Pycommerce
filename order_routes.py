"""
Order management route additions for web_server.py
"""

# Order management routes
@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    email: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for order management."""
    # Get selected tenant
    selected_tenant_slug = request.cookies.get("selected_tenant", None)
    selected_tenant = None
    
    # Try to get tenant data
    tenants = []
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
        
        if selected_tenant_slug:
            for t in tenants_list:
                if hasattr(t, 'slug') and t.slug == selected_tenant_slug:
                    selected_tenant = t
                    break
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
    
    # Initialize an empty list for orders
    orders = []
    from models import Order
    
    try:
        # Check if we have a tenant selected
        if selected_tenant and hasattr(selected_tenant, 'id'):
            # Build the query with filters
            query = Order.query.filter_by(tenant_id=str(selected_tenant.id))
            
            # Apply additional filters if provided
            if status:
                query = query.filter_by(status=status)
            
            if email:
                query = query.filter(Order.email.ilike(f"%{email}%"))
            
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, "%Y-%m-%d")
                    query = query.filter(Order.created_at >= from_date)
                except Exception as e:
                    logger.warning(f"Invalid date_from format: {str(e)}")
            
            if date_to:
                try:
                    to_date = datetime.strptime(date_to, "%Y-%m-%d")
                    # Make to_date inclusive by setting it to the end of the day
                    to_date = to_date.replace(hour=23, minute=59, second=59)
                    query = query.filter(Order.created_at <= to_date)
                except Exception as e:
                    logger.warning(f"Invalid date_to format: {str(e)}")
            
            # Get orders sorted by created_at in descending order (newest first)
            orders = query.order_by(Order.created_at.desc()).all()
            logger.info(f"Found {len(orders)} orders for tenant {selected_tenant.slug}")
        else:
            logger.warning("No tenant selected for orders page")
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
    
    # Prepare template parameters
    template_params = {
        "request": request,
        "active_page": "orders",
        "tenants": tenants,
        "selected_tenant": selected_tenant_slug,
        "orders": orders,
        "filter_status": status,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
        "filter_email": email,
        "status_message": status_message,
        "status_type": status_type
    }
    
    return templates.TemplateResponse("admin/orders.html", template_params)


@app.get("/admin/orders/{order_id}", response_class=HTMLResponse)
async def admin_order_detail(
    request: Request,
    order_id: str,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for viewing order details."""
    # Get selected tenant
    selected_tenant_slug = request.cookies.get("selected_tenant", None)
    
    # Try to get tenant data
    tenants = []
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
    
    # Get order details
    order = None
    from models import Order, OrderItem
    
    try:
        # Get the order with items
        order = Order.query.filter_by(id=order_id).first()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=danger",
                status_code=303
            )
        
        # Load order items with product details
        order_items = OrderItem.query.filter_by(order_id=order_id).all()
        for item in order_items:
            try:
                # Get product details if available
                from models import Product
                item.product = Product.query.filter_by(id=item.product_id).first()
            except Exception as e:
                logger.warning(f"Could not load product for order item: {str(e)}")
                item.product = None
        
        # Assign items to the order
        order.items = order_items
        
        # Get order notes
        try:
            from models import OrderNote
            notes = OrderNote.query.filter_by(order_id=order_id).order_by(OrderNote.created_at.desc()).all()
            order.notes = notes
            logger.info(f"Loaded {len(notes)} notes for order {order_id}")
        except Exception as e:
            logger.warning(f"Could not load order notes: {str(e)}")
            order.notes = []
        
        logger.info(f"Loaded order details for order {order_id}")
        
    except Exception as e:
        logger.error(f"Error fetching order details: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders?status_message=Error+loading+order+details&status_type=danger",
            status_code=303
        )
    
    # Prepare template parameters
    template_params = {
        "request": request,
        "active_page": "orders",
        "tenants": tenants,
        "selected_tenant": selected_tenant_slug,
        "order": order,
        "status_message": status_message,
        "status_type": status_type
    }
    
    return templates.TemplateResponse("admin/order_detail.html", template_params)


@app.get("/admin/orders/update-status/{order_id}", response_class=RedirectResponse)
async def admin_update_order_status(request: Request, order_id: str, status: str):
    """Update order status and redirect back to order details."""
    try:
        # Validate status
        valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
        if status not in valid_statuses:
            logger.warning(f"Invalid order status: {status}")
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?status_message=Invalid+status&status_type=danger",
                status_code=303
            )
        
        # Update order status
        from models import Order
        order = Order.query.filter_by(id=order_id).first()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=danger",
                status_code=303
            )
        
        # Update the status
        old_status = order.status
        order.status = status
        order.updated_at = datetime.utcnow()
        
        # You could also add an entry to an order history/log table here
        
        # Save the changes
        from app import db
        db.session.commit()
        
        logger.info(f"Updated order {order_id} status from {old_status} to {status}")
        
        # Redirect back to order details with success message
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Order+status+updated+successfully&status_type=success",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Error+updating+order+status&status_type=danger",
            status_code=303
        )


@app.post("/admin/orders/add-note/{order_id}", response_class=RedirectResponse)
async def admin_add_order_note(
    request: Request,
    order_id: str,
    content: str = Form(...),
    notify_customer: Optional[str] = Form(None),
    author: Optional[str] = Form(None)
):
    """Add a note to an order."""
    try:
        # Validate order exists
        from models import Order, OrderNote
        from app import db
        
        order = Order.query.filter_by(id=order_id).first()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=danger",
                status_code=303
            )
        
        # Check if we need to notify the customer
        is_customer_visible = notify_customer == "1"
        
        # Create and save the order note
        note = OrderNote(
            order_id=order_id,
            content=content,
            author=author or "Admin",  # Default to "Admin" if no author provided
            is_customer_visible=is_customer_visible
        )
        
        db.session.add(note)
        db.session.commit()
        
        logger.info(f"Added note to order {order_id}: {content}")
        
        if is_customer_visible:
            # In a real implementation, you'd send an email to the customer here
            logger.info(f"Would notify customer {order.email} about note: {content}")
        
        # Redirect back to order details with success message
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Note+added+successfully&status_type=success",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error adding order note: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Error+adding+note&status_type=danger",
            status_code=303
        )

