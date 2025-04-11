"""
API routes for product recommendations.

This module provides API endpoints for retrieving product recommendations
based on various criteria such as related products, personalized recommendations,
and trending products.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from pycommerce.models.product import Product
from pycommerce.services.recommendation import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    price: float
    sku: str
    stock: int = 0
    images: List[str] = []
    categories: List[str] = []
    
    class Config:
        from_attributes = True


class RecommendationsResponse(BaseModel):
    products: List[ProductResponse]
    count: int
    recommendation_type: str
    source_id: Optional[str] = None


@router.get("/related/{product_id}", response_model=RecommendationsResponse)
async def get_related_products(
    product_id: str,
    tenant_id: Optional[str] = Query(None, description="Optional tenant ID"),
    limit: int = Query(4, description="Maximum number of recommendations to return")
):
    """
    Get related products for a given product.
    
    Args:
        product_id: The ID of the product to find related items for
        tenant_id: Optional tenant ID for filtering products
        limit: Maximum number of recommendations to return
        
    Returns:
        List of related product recommendations
    """
    try:
        service = RecommendationService()
        related_products = service.get_related_products(product_id, limit, tenant_id)
        
        return RecommendationsResponse(
            products=[ProductResponse.from_orm(p) for p in related_products],
            count=len(related_products),
            recommendation_type="related",
            source_id=product_id
        )
    except Exception as e:
        logger.error(f"Error getting related products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting related products: {str(e)}")


@router.get("/personalized/{user_id}", response_model=RecommendationsResponse)
async def get_personalized_recommendations(
    user_id: str,
    tenant_id: Optional[str] = Query(None, description="Optional tenant ID"),
    limit: int = Query(8, description="Maximum number of recommendations to return")
):
    """
    Get personalized product recommendations for a user.
    
    Args:
        user_id: The ID of the user to get recommendations for
        tenant_id: Optional tenant ID for filtering products
        limit: Maximum number of recommendations to return
        
    Returns:
        List of personalized product recommendations
    """
    try:
        service = RecommendationService()
        recommendations = service.get_personalized_recommendations(user_id, limit, tenant_id)
        
        return RecommendationsResponse(
            products=[ProductResponse.from_orm(p) for p in recommendations],
            count=len(recommendations),
            recommendation_type="personalized",
            source_id=user_id
        )
    except Exception as e:
        logger.error(f"Error getting personalized recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting personalized recommendations: {str(e)}")


@router.get("/trending", response_model=RecommendationsResponse)
async def get_trending_products(
    tenant_id: Optional[str] = Query(None, description="Optional tenant ID"),
    limit: int = Query(8, description="Maximum number of recommendations to return")
):
    """
    Get trending products based on recent popularity.
    
    Args:
        tenant_id: Optional tenant ID for filtering products
        limit: Maximum number of trending products to return
        
    Returns:
        List of trending products
    """
    try:
        service = RecommendationService()
        trending_products = service.get_trending_products(limit, tenant_id)
        
        return RecommendationsResponse(
            products=[ProductResponse.from_orm(p) for p in trending_products],
            count=len(trending_products),
            recommendation_type="trending"
        )
    except Exception as e:
        logger.error(f"Error getting trending products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting trending products: {str(e)}")