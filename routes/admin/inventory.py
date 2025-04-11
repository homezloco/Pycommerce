# Handle "All Stores" selection
    if selected_tenant_slug.lower() == "all":
        # Show inventory for all tenants
        logger.info("Showing inventory for all tenants")
        try:
            # First try to get all tenants
            all_tenants = tenant_manager.list() or []

            # Then fetch inventory for each tenant and combine them
            all_items = []
            for tenant in all_tenants:
                try:
                    tenant_items = inventory_manager.get_by_tenant(
                        tenant_id=str(tenant.id),
                        **filters
                    )
                    all_items.extend(tenant_items)
                    logger.info(f"Found {len(tenant_items)} inventory items for tenant {tenant.name}")
                except Exception as e:
                    logger.error(f"Error fetching inventory for tenant {tenant.name}: {str(e)}")

            inventory_items = all_items
            logger.info(f"Found {len(inventory_items)} inventory items across all stores")

            # If no items found, fall back to list() method
            if not inventory_items:
                logger.info("No inventory items found using tenant queries, trying list() method")
                inventory_items = inventory_manager.list(**filters)
                logger.info(f"Found {len(inventory_items)} inventory items using list() method")

        except Exception as e:
            logger.error(f"Error fetching all inventory items: {str(e)}")
            # Fallback to the general list method
            inventory_items = inventory_manager.list(**filters)
            logger.info(f"Falling back to list() method, found {len(inventory_items)} inventory items")
    else:
        # Show inventory for specific tenant
        logger.info(f"Showing inventory for tenant: {tenant_obj.name}")