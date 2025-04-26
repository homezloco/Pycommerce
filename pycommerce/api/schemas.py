"""
API Schemas for PyCommerce.

This module defines Pydantic models for API request and response validation.
These models provide both runtime validation and OpenAPI schema generation.
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator, root_validator


class Error(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    field: Optional[str] = Field(None, description="Field with error (for validation errors)")


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status (e.g., 'ok', 'error')")
    version: str = Field(..., description="API version")
    message: str = Field(..., description="Additional status information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the health check")


class TenantBase(BaseModel):
    """Base model for tenant operations."""
    name: str = Field(..., description="Display name of the tenant")
    slug: str = Field(..., description="URL-friendly identifier for the tenant")
    domain: Optional[str] = Field(None, description="Custom domain for the tenant (if any)")
    active: bool = Field(True, description="Whether the tenant is active")


class TenantCreate(TenantBase):
    """Model for creating a new tenant."""
    pass


class TenantUpdate(BaseModel):
    """Model for updating a tenant."""
    name: Optional[str] = Field(None, description="Display name of the tenant")
    slug: Optional[str] = Field(None, description="URL-friendly identifier for the tenant")
    domain: Optional[str] = Field(None, description="Custom domain for the tenant")
    active: Optional[bool] = Field(None, description="Whether the tenant is active")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant-specific settings")


class Tenant(TenantBase):
    """Complete tenant model with all fields."""
    id: str = Field(..., description="Unique identifier for the tenant")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant-specific settings")
    created_at: datetime = Field(..., description="When the tenant was created")
    updated_at: Optional[datetime] = Field(None, description="When the tenant was last updated")

    class Config:
        orm_mode = True


class TenantList(BaseModel):
    """List of tenants with count."""
    tenants: List[Tenant] = Field(..., description="List of tenants")
    count: int = Field(..., description="Total number of tenants")


class CategoryBase(BaseModel):
    """Base model for category operations."""
    name: str = Field(..., description="Name of the category")
    slug: str = Field(..., description="URL-friendly identifier for the category")
    description: Optional[str] = Field(None, description="Description of the category")
    parent_id: Optional[str] = Field(None, description="ID of the parent category (if any)")


class CategoryCreate(CategoryBase):
    """Model for creating a new category."""
    tenant_id: str = Field(..., description="ID of the tenant this category belongs to")


class CategoryUpdate(BaseModel):
    """Model for updating a category."""
    name: Optional[str] = Field(None, description="Name of the category")
    slug: Optional[str] = Field(None, description="URL-friendly identifier for the category")
    description: Optional[str] = Field(None, description="Description of the category")
    parent_id: Optional[str] = Field(None, description="ID of the parent category")


class Category(CategoryBase):
    """Complete category model with all fields."""
    id: str = Field(..., description="Unique identifier for the category")
    tenant_id: str = Field(..., description="ID of the tenant this category belongs to")
    created_at: datetime = Field(..., description="When the category was created")
    updated_at: Optional[datetime] = Field(None, description="When the category was last updated")
    
    class Config:
        orm_mode = True


class CategoryList(BaseModel):
    """List of categories with count."""
    categories: List[Category] = Field(..., description="List of categories")
    count: int = Field(..., description="Total number of categories")


class ProductBase(BaseModel):
    """Base model for product operations."""
    name: str = Field(..., description="Name of the product")
    description: Optional[str] = Field(None, description="Description of the product")
    price: float = Field(..., ge=0, description="Price of the product")
    sku: str = Field(..., description="Stock keeping unit (unique product identifier)")
    stock: int = Field(0, ge=0, description="Current stock level")
    cost_price: Optional[float] = Field(None, ge=0, description="Cost price for profit calculation")
    is_material: Optional[bool] = Field(False, description="Whether this product is a material")
    is_labor: Optional[bool] = Field(False, description="Whether this product represents labor")
    labor_rate: Optional[float] = Field(None, ge=0, description="Hourly rate if this is labor")


class ProductCreate(ProductBase):
    """Model for creating a new product."""
    tenant_id: str = Field(..., description="ID of the tenant this product belongs to")
    categories: Optional[List[str]] = Field([], description="List of category IDs this product belongs to")


class ProductUpdate(BaseModel):
    """Model for updating a product."""
    name: Optional[str] = Field(None, description="Name of the product")
    description: Optional[str] = Field(None, description="Description of the product")
    price: Optional[float] = Field(None, ge=0, description="Price of the product")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    stock: Optional[int] = Field(None, ge=0, description="Current stock level")
    categories: Optional[List[str]] = Field(None, description="List of category IDs")
    cost_price: Optional[float] = Field(None, ge=0, description="Cost price for profit calculation")
    is_material: Optional[bool] = Field(None, description="Whether this product is a material")
    is_labor: Optional[bool] = Field(None, description="Whether this product represents labor")
    labor_rate: Optional[float] = Field(None, ge=0, description="Hourly rate if this is labor")


class Product(ProductBase):
    """Complete product model with all fields."""
    id: str = Field(..., description="Unique identifier for the product")
    tenant_id: str = Field(..., description="ID of the tenant this product belongs to")
    categories: List[str] = Field([], description="List of category IDs this product belongs to")
    created_at: datetime = Field(..., description="When the product was created")
    updated_at: Optional[datetime] = Field(None, description="When the product was last updated")
    
    class Config:
        orm_mode = True


class ProductList(BaseModel):
    """List of products with count and filters."""
    products: List[Product] = Field(..., description="List of products")
    tenant: str = Field(..., description="Tenant identifier")
    count: int = Field(..., description="Total number of products")
    filters: Dict[str, Any] = Field({}, description="Applied filters")


class OrderItemBase(BaseModel):
    """Base model for order item operations."""
    product_id: str = Field(..., description="ID of the product")
    quantity: int = Field(..., gt=0, description="Quantity of the product")
    price: float = Field(..., ge=0, description="Price at time of order")
    name: str = Field(..., description="Product name at time of order")
    sku: str = Field(..., description="Product SKU at time of order")
    cost_price: Optional[float] = Field(None, ge=0, description="Cost price at time of order")
    is_material: Optional[bool] = Field(False, description="Whether this item is a material")
    is_labor: Optional[bool] = Field(False, description="Whether this item represents labor")
    hours: Optional[float] = Field(None, ge=0, description="Number of labor hours if applicable")
    labor_rate: Optional[float] = Field(None, ge=0, description="Hourly rate for labor if applicable")


class OrderItem(OrderItemBase):
    """Complete order item model with all fields."""
    id: str = Field(..., description="Unique identifier for the order item")
    order_id: str = Field(..., description="ID of the order this item belongs to")
    
    class Config:
        orm_mode = True


class Address(BaseModel):
    """Address model for shipping and billing."""
    name: str = Field(..., description="Full name")
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State or province")
    postal_code: str = Field(..., description="Postal code or ZIP")
    country: str = Field(..., description="Country")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Contact email address")


class OrderBase(BaseModel):
    """Base model for order operations."""
    user_id: Optional[str] = Field(None, description="ID of the user who placed the order (if any)")
    status: str = Field("pending", description="Order status (pending, processing, shipped, etc.)")
    shipping_address: Address = Field(..., description="Shipping address")
    billing_address: Optional[Address] = Field(None, description="Billing address (if different from shipping)")
    shipping_method: Optional[str] = Field(None, description="Selected shipping method")
    payment_status: Optional[str] = Field("unpaid", description="Payment status")
    notes: Optional[str] = Field(None, description="Internal order notes")


class OrderCreate(OrderBase):
    """Model for creating a new order."""
    tenant_id: str = Field(..., description="ID of the tenant this order belongs to")
    items: List[OrderItemBase] = Field(..., min_items=1, description="List of items in the order")


class OrderUpdate(BaseModel):
    """Model for updating an order."""
    status: Optional[str] = Field(None, description="Order status")
    shipping_address: Optional[Address] = Field(None, description="Shipping address")
    billing_address: Optional[Address] = Field(None, description="Billing address")
    shipping_method: Optional[str] = Field(None, description="Selected shipping method")
    payment_status: Optional[str] = Field(None, description="Payment status")
    notes: Optional[str] = Field(None, description="Internal order notes")


class Order(OrderBase):
    """Complete order model with all fields."""
    id: str = Field(..., description="Unique identifier for the order")
    tenant_id: str = Field(..., description="ID of the tenant this order belongs to")
    items: List[OrderItem] = Field(..., description="List of items in the order")
    total: float = Field(..., description="Total amount of the order")
    created_at: datetime = Field(..., description="When the order was created")
    updated_at: Optional[datetime] = Field(None, description="When the order was last updated")
    total_cost: Optional[float] = Field(None, description="Combined cost of materials and labor")
    materials_cost: Optional[float] = Field(None, description="Total cost of materials only")
    labor_cost: Optional[float] = Field(None, description="Total cost of labor only")
    profit: Optional[float] = Field(None, description="Total profit (total - total_cost)")
    profit_margin: Optional[float] = Field(None, description="Percentage of profit relative to total")
    
    @validator('profit', always=True)
    def calculate_profit(cls, v, values):
        """Calculate profit if total and total_cost are available."""
        if v is not None:
            return v
        
        total = values.get('total')
        total_cost = values.get('total_cost')
        
        if total is not None and total_cost is not None:
            return total - total_cost
        
        return None
    
    @validator('profit_margin', always=True)
    def calculate_profit_margin(cls, v, values):
        """Calculate profit margin if total and profit are available."""
        if v is not None:
            return v
        
        total = values.get('total')
        profit = values.get('profit')
        
        if total is not None and profit is not None and total > 0:
            return (profit / total) * 100
        
        return None
    
    class Config:
        orm_mode = True


class OrderList(BaseModel):
    """List of orders with count."""
    orders: List[Order] = Field(..., description="List of orders")
    count: int = Field(..., description="Total number of orders")


class UserBase(BaseModel):
    """Base model for user operations."""
    email: EmailStr = Field(..., description="Email address (used for login)")
    username: str = Field(..., description="Username")
    role: str = Field("customer", description="User role (admin, customer, etc.)")
    active: bool = Field(True, description="Whether the user account is active")


class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8, description="User password")
    tenant_id: str = Field(..., description="ID of the tenant this user belongs to")


class UserUpdate(BaseModel):
    """Model for updating a user."""
    email: Optional[EmailStr] = Field(None, description="Email address")
    username: Optional[str] = Field(None, description="Username")
    role: Optional[str] = Field(None, description="User role")
    active: Optional[bool] = Field(None, description="Whether the user account is active")
    password: Optional[str] = Field(None, min_length=8, description="New password (if changing)")


class User(UserBase):
    """Complete user model with all fields (except password)."""
    id: str = Field(..., description="Unique identifier for the user")
    tenant_id: str = Field(..., description="ID of the tenant this user belongs to")
    created_at: datetime = Field(..., description="When the user was created")
    last_login: Optional[datetime] = Field(None, description="When the user last logged in")
    
    class Config:
        orm_mode = True


class UserList(BaseModel):
    """List of users with count."""
    users: List[User] = Field(..., description="List of users")
    count: int = Field(..., description="Total number of users")


class Token(BaseModel):
    """JWT token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token (if applicable)")


class TokenData(BaseModel):
    """JWT token data model."""
    sub: str = Field(..., description="Subject (usually user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    tenant_id: str = Field(..., description="Tenant ID")
    role: str = Field(..., description="User role")


class MediaBase(BaseModel):
    """Base model for media operations."""
    name: str = Field(..., description="Name of the media file")
    type: str = Field(..., description="Media type (image, document, etc.)")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Additional metadata")
    sharing_level: str = Field("tenant", description="Access control level (tenant, global)")


class MediaCreate(MediaBase):
    """Model for creating a new media entry."""
    tenant_id: str = Field(..., description="ID of the tenant this media belongs to")
    # Content is handled separately in multipart form data


class MediaUpdate(BaseModel):
    """Model for updating a media entry."""
    name: Optional[str] = Field(None, description="Name of the media file")
    type: Optional[str] = Field(None, description="Media type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    sharing_level: Optional[str] = Field(None, description="Access control level")


class Media(MediaBase):
    """Complete media model with all fields."""
    id: str = Field(..., description="Unique identifier for the media")
    tenant_id: str = Field(..., description="ID of the tenant this media belongs to")
    path: str = Field(..., description="Storage path")
    url: str = Field(..., description="Access URL")
    created_at: datetime = Field(..., description="When the media was uploaded")
    
    class Config:
        orm_mode = True


class MediaList(BaseModel):
    """List of media with count."""
    media: List[Media] = Field(..., description="List of media files")
    count: int = Field(..., description="Total number of media files")


class PageSectionBase(BaseModel):
    """Base model for page section operations."""
    type: str = Field(..., description="Section type identifier")
    title: Optional[str] = Field(None, description="Section title (if applicable)")
    order: int = Field(0, description="Display order within the page")
    settings: Optional[Dict[str, Any]] = Field({}, description="Section-specific settings")


class ContentBlockBase(BaseModel):
    """Base model for content block operations."""
    type: str = Field(..., description="Block type identifier")
    content: Dict[str, Any] = Field(..., description="Block content data")
    order: int = Field(0, description="Display order within the section")
    settings: Optional[Dict[str, Any]] = Field({}, description="Block-specific settings")


class PageBase(BaseModel):
    """Base model for page operations."""
    title: str = Field(..., description="Page title")
    slug: str = Field(..., description="URL path")
    status: str = Field("draft", description="Publication status (draft, published)")
    template_id: Optional[str] = Field(None, description="ID of the page template (if any)")


class PageCreate(PageBase):
    """Model for creating a new page."""
    tenant_id: str = Field(..., description="ID of the tenant this page belongs to")


class PageSection(PageSectionBase):
    """Complete page section model with all fields."""
    id: str = Field(..., description="Unique identifier for the section")
    page_id: str = Field(..., description="ID of the page this section belongs to")
    blocks: List[ContentBlockBase] = Field([], description="Content blocks in this section")
    
    class Config:
        orm_mode = True


class Page(PageBase):
    """Complete page model with all fields."""
    id: str = Field(..., description="Unique identifier for the page")
    tenant_id: str = Field(..., description="ID of the tenant this page belongs to")
    sections: List[PageSection] = Field([], description="Sections in this page")
    created_at: datetime = Field(..., description="When the page was created")
    updated_at: Optional[datetime] = Field(None, description="When the page was last updated")
    
    class Config:
        orm_mode = True


class PageList(BaseModel):
    """List of pages with count."""
    pages: List[Page] = Field(..., description="List of pages")
    count: int = Field(..., description="Total number of pages")


class PageTemplateBase(BaseModel):
    """Base model for page template operations."""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    thumbnail: Optional[str] = Field(None, description="URL to template thumbnail image")
    type: str = Field("standard", description="Template type (standard, advanced)")


class PageTemplate(PageTemplateBase):
    """Complete page template model with all fields."""
    id: str = Field(..., description="Unique identifier for the template")
    sections: List[Dict[str, Any]] = Field([], description="Default sections for this template")
    created_at: datetime = Field(..., description="When the template was created")
    updated_at: Optional[datetime] = Field(None, description="When the template was last updated")
    
    class Config:
        orm_mode = True


class PageTemplateList(BaseModel):
    """List of page templates with count."""
    templates: List[PageTemplate] = Field(..., description="List of page templates")
    count: int = Field(..., description="Total number of templates")


class PaymentMethodBase(BaseModel):
    """Base model for payment method operations."""
    provider: str = Field(..., description="Payment provider (stripe, paypal, etc.)")
    is_default: bool = Field(False, description="Whether this is the default payment method")
    is_enabled: bool = Field(True, description="Whether this payment method is enabled")
    settings: Dict[str, Any] = Field({}, description="Provider-specific settings")


class PaymentMethod(PaymentMethodBase):
    """Complete payment method model with all fields."""
    id: str = Field(..., description="Unique identifier for the payment method")
    tenant_id: str = Field(..., description="ID of the tenant this payment method belongs to")
    created_at: datetime = Field(..., description="When the payment method was created")
    updated_at: Optional[datetime] = Field(None, description="When the payment method was last updated")
    
    class Config:
        orm_mode = True


class ShippingMethodBase(BaseModel):
    """Base model for shipping method operations."""
    name: str = Field(..., description="Shipping method name")
    description: Optional[str] = Field(None, description="Description of the shipping method")
    price: float = Field(..., ge=0, description="Base price for this shipping method")
    is_enabled: bool = Field(True, description="Whether this shipping method is enabled")
    settings: Dict[str, Any] = Field({}, description="Method-specific settings")


class ShippingMethod(ShippingMethodBase):
    """Complete shipping method model with all fields."""
    id: str = Field(..., description="Unique identifier for the shipping method")
    tenant_id: str = Field(..., description="ID of the tenant this shipping method belongs to")
    created_at: datetime = Field(..., description="When the shipping method was created")
    updated_at: Optional[datetime] = Field(None, description="When the shipping method was last updated")
    
    class Config:
        orm_mode = True


class EstimateItemBase(BaseModel):
    """Base model for estimate item operations."""
    description: str = Field(..., description="Item description")
    quantity: float = Field(..., gt=0, description="Quantity")
    price: float = Field(..., ge=0, description="Unit price")
    is_material: bool = Field(False, description="Whether this is a material item")
    is_labor: bool = Field(False, description="Whether this is a labor item")
    labor_rate: Optional[float] = Field(None, ge=0, description="Hourly rate if this is labor")
    hours: Optional[float] = Field(None, ge=0, description="Number of hours if this is labor")


class EstimateItem(EstimateItemBase):
    """Complete estimate item model with all fields."""
    id: str = Field(..., description="Unique identifier for the estimate item")
    estimate_id: str = Field(..., description="ID of the estimate this item belongs to")
    subtotal: float = Field(..., description="Item subtotal (quantity * price)")
    
    @validator('subtotal', always=True)
    def calculate_subtotal(cls, v, values):
        """Calculate subtotal from quantity and price."""
        quantity = values.get('quantity')
        price = values.get('price')
        
        if quantity is not None and price is not None:
            return quantity * price
        
        return v
    
    class Config:
        orm_mode = True


class EstimateBase(BaseModel):
    """Base model for estimate operations."""
    customer_name: str = Field(..., description="Customer name")
    customer_email: EmailStr = Field(..., description="Customer email")
    status: str = Field("draft", description="Estimate status (draft, sent, approved)")
    notes: Optional[str] = Field(None, description="Internal notes about the estimate")


class EstimateCreate(EstimateBase):
    """Model for creating a new estimate."""
    tenant_id: str = Field(..., description="ID of the tenant this estimate belongs to")
    items: List[EstimateItemBase] = Field(..., min_items=1, description="List of items in the estimate")


class EstimateUpdate(BaseModel):
    """Model for updating an estimate."""
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email")
    status: Optional[str] = Field(None, description="Estimate status")
    notes: Optional[str] = Field(None, description="Internal notes")


class Estimate(EstimateBase):
    """Complete estimate model with all fields."""
    id: str = Field(..., description="Unique identifier for the estimate")
    tenant_id: str = Field(..., description="ID of the tenant this estimate belongs to")
    items: List[EstimateItem] = Field(..., description="List of items in the estimate")
    total: float = Field(..., description="Total amount of the estimate")
    created_at: datetime = Field(..., description="When the estimate was created")
    updated_at: Optional[datetime] = Field(None, description="When the estimate was last updated")
    materials_cost: Optional[float] = Field(None, description="Total cost of materials")
    labor_cost: Optional[float] = Field(None, description="Total cost of labor")
    profit: Optional[float] = Field(None, description="Calculated profit")
    profit_margin: Optional[float] = Field(None, description="Percentage profit margin")
    
    @validator('total', always=True)
    def calculate_total(cls, v, values):
        """Calculate total from items if not provided."""
        if v is not None:
            return v
        
        items = values.get('items', [])
        if items:
            return sum(item.subtotal for item in items)
        
        return 0.0
    
    class Config:
        orm_mode = True


class EstimateList(BaseModel):
    """List of estimates with count."""
    estimates: List[Estimate] = Field(..., description="List of estimates")
    count: int = Field(..., description="Total number of estimates")