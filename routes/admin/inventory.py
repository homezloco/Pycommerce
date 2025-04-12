# Handle "All Stores" selection
    if selected_tenant_slug.lower() == "all":
        # Show inventory for all tenants
        from routes.admin.tenant_utils import get_items_for_all_tenants
        logger.info("Showing inventory for all tenants")

        inventory_items = get_items_for_all_tenants(
            tenant_manager=tenant_manager,
            item_manager=inventory_manager,
            get_method_name='get_by_tenant',
            logger=logger,
            filters=filters
        )
    else:
        # Show inventory for specific tenant
        logger.info(f"Showing inventory for tenant: {tenant_obj.name}")