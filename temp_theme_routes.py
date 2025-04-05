# Admin theme settings
@app.get("/admin/theme-settings", response_class=HTMLResponse)
async def admin_theme_settings(request: Request, status_message: Optional[str] = None, status_type: str = "info"):
    """Admin page for managing theme settings."""
    # Get all tenants for the store selector
    tenants = []
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain if hasattr(t, 'domain') else None,
                "active": t.active if hasattr(t, 'active') else True
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
        
        # Get selected tenant from query param
        selected_tenant_slug = request.query_params.get('tenant')
        if not selected_tenant_slug and tenants:
            selected_tenant_slug = tenants[0]["slug"]
            
        # Get the tenant details
        tenant = None
        theme_settings = {}
        if selected_tenant_slug:
            tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
            if tenant_obj:
                tenant = {
                    "id": str(tenant_obj.id),
                    "name": tenant_obj.name,
                    "slug": tenant_obj.slug,
                    "domain": tenant_obj.domain,
                    "active": tenant_obj.active
                }
                
                # Get theme settings from tenant settings
                if hasattr(tenant_obj, 'settings') and tenant_obj.settings:
                    if 'theme' in tenant_obj.settings:
                        theme_settings = tenant_obj.settings['theme']
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Error loading theme settings: {str(e)}")
        if status_message is None:
            status_message = f"Error loading theme settings: {str(e)}"
            status_type = "danger"
    
    return templates.TemplateResponse(
        "admin/theme_settings.html", 
        {
            "request": request,
            "active_page": "theme_settings",
            "tenants": tenants,
            "tenant": tenant,
            "theme": theme_settings,
            "cart_item_count": cart_item_count,
            "success": status_message if status_type == "success" else None,
            "error": status_message if status_type == "danger" else None
        }
    )

@app.post("/admin/theme-settings", response_class=RedirectResponse)
async def admin_save_theme_settings(request: Request):
    """Save theme settings for a tenant."""
    try:
        form_data = await request.form()
        
        # Get the selected tenant from the query parameters
        selected_tenant_slug = request.query_params.get('tenant')
        
        if not selected_tenant_slug:
            raise ValueError("No tenant selected")
        
        # Get the tenant
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant_obj:
            raise ValueError(f"Tenant not found: {selected_tenant_slug}")
        
        # Create theme settings dictionary
        theme_settings = {
            # Colors
            "primary_color": form_data.get("primary_color", "#007bff"),
            "secondary_color": form_data.get("secondary_color", "#6c757d"),
            "background_color": form_data.get("background_color", "#ffffff"),
            "text_color": form_data.get("text_color", "#212529"),
            
            # Typography
            "font_family": form_data.get("font_family", "'Open Sans', sans-serif"),
            "heading_font_family": form_data.get("heading_font_family", "inherit"),
            "base_font_size": int(form_data.get("base_font_size", "16")),
            "heading_scale": form_data.get("heading_scale", "moderate"),
            
            # Layout
            "container_width": form_data.get("container_width", "standard"),
            "border_radius": int(form_data.get("border_radius", "4")),
            "spacing_scale": form_data.get("spacing_scale", "moderate"),
            
            # Store Elements
            "header_style": form_data.get("header_style", "standard"),
            "product_card_style": form_data.get("product_card_style", "standard"),
            "button_style": form_data.get("button_style", "standard"),
            
            # Custom CSS
            "custom_css": form_data.get("custom_css", ""),
            
            # Updated timestamp
            "updated_at": datetime.now().isoformat()
        }
        
        # Update tenant theme settings
        tenant_manager.update_theme(tenant_obj.id, theme_settings)
        
        status_message = "Theme settings saved successfully"
        status_type = "success"
    except Exception as e:
        logger.error(f"Error saving theme settings: {str(e)}")
        status_message = f"Error saving theme settings: {str(e)}"
        status_type = "danger"
    
    # Redirect back to the theme settings page
    redirect_url = f"/admin/theme-settings?tenant={selected_tenant_slug}&status_message={status_message}&status_type={status_type}"
    return RedirectResponse(url=redirect_url, status_code=303)