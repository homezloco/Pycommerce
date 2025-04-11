# Handle "All Stores" selection
    if selected_tenant_slug.lower() == "all":
        try:
            # First try to get all tenants
            all_tenants = tenant_manager.list() or []

            # Then fetch products for each tenant and combine them
            all_products = []
            for tenant in all_tenants:
                try:
                    tenant_products = product_manager.get_by_tenant(
                        tenant_id=str(tenant.id)
                    )
                    all_products.extend(tenant_products)
                    logger.info(f"Found {len(tenant_products)} products for tenant {tenant.name}")
                except Exception as e:
                    logger.error(f"Error fetching products for tenant {tenant.name}: {str(e)}")

            products = all_products
            logger.info(f"Fetched {len(products)} products across all stores")

            # If no products found, fall back to list() method
            if not products:
                logger.info("No products found using tenant queries, trying list() method")
                products = product_manager.list()
                logger.info(f"Found {len(products)} products using list() method")
        except Exception as e:
            logger.error(f"Error fetching all products: {str(e)}")
            # Fallback to the general list method
            products = product_manager.list()
            logger.info(f"Falling back to list() method, found {len(products)} products")
    else:
        products = product_manager.get_by_tenant(str(tenant_obj.id))
        logger.info(f"Fetching inventory for tenant: {tenant_obj.name}")