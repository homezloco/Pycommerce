# Get selected tenant from request parameters or use the first tenant
from fastapi import Request

async def get_inventory_items(request: Request, tenant_manager, inventory_manager, filters=None):
    tenants = tenant_manager.list()
    selected_tenant_slug = request.query_params.get('tenant', None)
    if not selected_tenant_slug and tenants:
        selected_tenant_slug = tenants[0].slug
    
    # Get the tenant object
    tenant_obj = None
    if selected_tenant_slug and selected_tenant_slug.lower() != "all":
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)

    # Handle "All Stores" selection
    if selected_tenant_slug and selected_tenant_slug.lower() == "all":
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