"""
Product recommendation service for PyCommerce.

This module provides AI-powered product recommendation functionality,
suggesting relevant products based on user behavior, purchase history,
and product similarity.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pycommerce.models.product import Product, ProductManager
from pycommerce.plugins.ai.config import get_ai_provider_instance

logger = logging.getLogger(__name__)


class RecommendationService:
    """Provides product recommendation functionality."""
    
    def __init__(self):
        """Initialize the recommendation service."""
        self.product_manager = ProductManager()
    
    def get_related_products(self, product_id: Union[str, UUID], limit: int = 4, tenant_id: Optional[str] = None) -> List[Product]:
        """
        Get related products for a given product.
        
        Args:
            product_id: The ID of the product to find related items for
            limit: Maximum number of recommendations to return
            tenant_id: Optional tenant ID for recommendations
            
        Returns:
            List of recommended products
        """
        try:
            # Get the product details
            product = self.product_manager.get(product_id)
            if not product:
                logger.warning(f"Product not found: {product_id}")
                return []
            
            # Simple category-based recommendation first
            similar_products = self._get_category_based_recommendations(product, limit, tenant_id)
            
            # If we don't have enough recommendations, try AI-based recommendations
            if len(similar_products) < limit:
                ai_recommendations = self._get_ai_based_recommendations(product, limit - len(similar_products), tenant_id)
                # Merge recommendations, avoiding duplicates
                for rec in ai_recommendations:
                    if rec.id != product.id and rec not in similar_products:
                        similar_products.append(rec)
                        if len(similar_products) >= limit:
                            break
            
            return similar_products[:limit]
        
        except Exception as e:
            logger.error(f"Error getting related products: {str(e)}")
            return []
    
    def get_personalized_recommendations(self, user_id: str, limit: int = 8, tenant_id: Optional[str] = None) -> List[Product]:
        """
        Get personalized product recommendations for a user.
        
        Args:
            user_id: The ID of the user to get recommendations for
            limit: Maximum number of recommendations to return
            tenant_id: Optional tenant ID for recommendations
            
        Returns:
            List of recommended products
        """
        try:
            # Get user's purchase history and recently viewed products
            # This would normally come from a user activity tracking system
            # For now, return category-based recommendations for available products
            
            # Get some products from the tenant
            tenant_products = self.product_manager.get_by_tenant(tenant_id) if tenant_id else []
            
            # If we have no products, return empty list
            if not tenant_products:
                return []
            
            # Get some variety by using the first product's categories
            if tenant_products:
                seed_product = tenant_products[0]
                recommendations = self._get_category_based_recommendations(seed_product, limit, tenant_id)
                
                # If we don't have enough, add some AI recommendations
                if len(recommendations) < limit:
                    remaining = limit - len(recommendations)
                    ai_recs = self._get_ai_based_user_recommendations(user_id, remaining, tenant_id)
                    
                    # Merge recommendations, avoiding duplicates
                    for rec in ai_recs:
                        if rec not in recommendations:
                            recommendations.append(rec)
                            if len(recommendations) >= limit:
                                break
                
                return recommendations[:limit]
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {str(e)}")
            return []
    
    def get_trending_products(self, limit: int = 8, tenant_id: Optional[str] = None) -> List[Product]:
        """
        Get trending products based on recent popularity.
        
        Args:
            limit: Maximum number of trending products to return
            tenant_id: Optional tenant ID to filter products by
            
        Returns:
            List of trending products
        """
        try:
            # In a production system, this would use actual sales/view data
            # For now, return the most recently added products for the tenant
            
            # Get products for the tenant
            products = self.product_manager.get_by_tenant(tenant_id) if tenant_id else []
            
            # Sort by created_at (descending)
            sorted_products = sorted(products, key=lambda p: p.created_at, reverse=True)
            
            return sorted_products[:limit]
        
        except Exception as e:
            logger.error(f"Error getting trending products: {str(e)}")
            return []
    
    def _get_category_based_recommendations(self, product: Product, limit: int, tenant_id: Optional[str] = None) -> List[Product]:
        """
        Get products in the same categories as the given product.
        
        Args:
            product: The product to find similar items for
            limit: Maximum number of recommendations to return
            tenant_id: Optional tenant ID for recommendations
            
        Returns:
            List of recommended products
        """
        if not product.categories:
            return []
        
        # Get all products for the tenant
        all_products = self.product_manager.get_by_tenant(tenant_id) if tenant_id else []
        
        # Filter out the original product
        all_products = [p for p in all_products if str(p.id) != str(product.id)]
        
        # Calculate category similarity scores
        scored_products = []
        for p in all_products:
            # Count how many categories are shared
            shared_categories = set(p.categories).intersection(set(product.categories))
            if shared_categories:
                scored_products.append((p, len(shared_categories)))
        
        # Sort by similarity score (descending)
        sorted_products = [p for p, score in sorted(scored_products, key=lambda x: x[1], reverse=True)]
        
        return sorted_products[:limit]
    
    def _get_ai_based_recommendations(self, product: Product, limit: int, tenant_id: Optional[str] = None) -> List[Product]:
        """
        Use AI to find similar products based on content similarity.
        
        Args:
            product: The product to find similar items for
            limit: Maximum number of recommendations to return
            tenant_id: Optional tenant ID for recommendations
            
        Returns:
            List of AI-recommended products
        """
        try:
            # Get all products for the tenant
            all_products = self.product_manager.get_by_tenant(tenant_id) if tenant_id else []
            
            # Filter out the original product
            candidate_products = [p for p in all_products if str(p.id) != str(product.id)]
            
            # If we have very few products, just return them
            if len(candidate_products) <= limit:
                return candidate_products
            
            # Try to get an AI provider instance
            try:
                ai_provider = get_ai_provider_instance(tenant_id)
            except Exception as e:
                logger.warning(f"Could not get AI provider for recommendations: {str(e)}")
                # Return random products if AI is not available
                import random
                random.shuffle(candidate_products)
                return candidate_products[:limit]
            
            # Prepare product info for the AI prompt
            product_info = (
                f"Product ID: {product.id}\n"
                f"Name: {product.name}\n"
                f"Description: {product.description}\n"
                f"Categories: {', '.join(product.categories)}\n"
                f"Price: ${product.price:.2f}"
            )
            
            # Create a list of candidate product info
            candidate_info = []
            for i, p in enumerate(candidate_products[:20]):  # Limit to 20 candidates for prompt size
                candidate_info.append(
                    f"[{i+1}] Product ID: {p.id}\n"
                    f"Name: {p.name}\n"
                    f"Description: {p.description}\n"
                    f"Categories: {', '.join(p.categories)}\n"
                    f"Price: ${p.price:.2f}"
                )
            
            # Create the AI prompt
            prompt = (
                f"You are a product recommendation system for an e-commerce platform. "
                f"I'll give you details about a product and a list of candidate products. "
                f"Your task is to select the most similar or complementary products that would interest someone viewing the main product.\n\n"
                f"MAIN PRODUCT:\n{product_info}\n\n"
                f"CANDIDATE PRODUCTS:\n" + "\n\n".join(candidate_info) + "\n\n"
                f"Please provide the numbers (e.g., [1], [5], [10]) of the {limit} most suitable products to recommend, "
                f"based on similarity, complementary nature, or typical purchase patterns. Only reply with the numbers, nothing else."
            )
            
            # Get AI recommendation
            try:
                response = ai_provider.generate_text(prompt)
                
                # Parse the response to get the recommended product indices
                import re
                index_matches = re.findall(r'\[(\d+)\]', response)
                
                # Convert to integers and filter out invalid indices
                try:
                    indices = [int(idx) - 1 for idx in index_matches if 0 < int(idx) <= len(candidate_products)]
                except ValueError:
                    indices = []
                
                # Get the recommended products
                recommendations = []
                for idx in indices:
                    if 0 <= idx < len(candidate_products):
                        recommendations.append(candidate_products[idx])
                
                return recommendations[:limit]
                
            except Exception as e:
                logger.error(f"Error getting AI recommendations: {str(e)}")
                # Return random products if AI recommendation fails
                import random
                random.shuffle(candidate_products)
                return candidate_products[:limit]
                
        except Exception as e:
            logger.error(f"Error in AI-based recommendations: {str(e)}")
            return []
    
    def _get_ai_based_user_recommendations(self, user_id: str, limit: int, tenant_id: Optional[str] = None) -> List[Product]:
        """
        Use AI to generate personalized recommendations for a user.
        
        Args:
            user_id: The ID of the user to get recommendations for
            limit: Maximum number of recommendations to return
            tenant_id: Optional tenant ID for recommendations
            
        Returns:
            List of AI-recommended products
        """
        try:
            # Get all products for the tenant
            all_products = self.product_manager.get_by_tenant(tenant_id) if tenant_id else []
            
            # If we have very few products, just return them
            if len(all_products) <= limit:
                return all_products
            
            # Try to get an AI provider instance
            try:
                ai_provider = get_ai_provider_instance(tenant_id)
            except Exception as e:
                logger.warning(f"Could not get AI provider for user recommendations: {str(e)}")
                # Return random products if AI is not available
                import random
                random.shuffle(all_products)
                return all_products[:limit]
            
            # In a real system, we would fetch the user's purchase history, browsing history, etc.
            # For demonstration, we'll use a hypothetical user profile
            
            # Select a subset of products as candidates
            import random
            candidate_products = random.sample(all_products, min(20, len(all_products)))
            
            # Create a list of candidate product info
            candidate_info = []
            for i, p in enumerate(candidate_products):
                candidate_info.append(
                    f"[{i+1}] Product ID: {p.id}\n"
                    f"Name: {p.name}\n"
                    f"Description: {p.description}\n"
                    f"Categories: {', '.join(p.categories)}\n"
                    f"Price: ${p.price:.2f}"
                )
            
            # Create the AI prompt
            prompt = (
                f"You are a product recommendation system for an e-commerce platform. "
                f"I'll give you a list of products. Your task is to select a diverse set of {limit} products "
                f"that would appeal to different customer preferences and represent a good mix of categories.\n\n"
                f"PRODUCTS:\n" + "\n\n".join(candidate_info) + "\n\n"
                f"Please provide the numbers (e.g., [1], [5], [10]) of the {limit} most suitable products to recommend, "
                f"ensuring diversity across categories and price points. Only reply with the numbers, nothing else."
            )
            
            # Get AI recommendation
            try:
                response = ai_provider.generate_text(prompt)
                
                # Parse the response to get the recommended product indices
                import re
                index_matches = re.findall(r'\[(\d+)\]', response)
                
                # Convert to integers and filter out invalid indices
                try:
                    indices = [int(idx) - 1 for idx in index_matches if 0 < int(idx) <= len(candidate_products)]
                except ValueError:
                    indices = []
                
                # Get the recommended products
                recommendations = []
                for idx in indices:
                    if 0 <= idx < len(candidate_products):
                        recommendations.append(candidate_products[idx])
                
                return recommendations[:limit]
                
            except Exception as e:
                logger.error(f"Error getting AI user recommendations: {str(e)}")
                # Return random products if AI recommendation fails
                random.shuffle(candidate_products)
                return candidate_products[:limit]
                
        except Exception as e:
            logger.error(f"Error in AI-based user recommendations: {str(e)}")
            return []