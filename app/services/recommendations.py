"""
Advanced Recommendations Service
Uses vector similarity for intelligent product recommendations
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import numpy as np
from collections import defaultdict
from sqlalchemy import case

from app.models import Product, Swipe, User
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

# Cache functions for recommendations
def get_cached_recommendations(user_id: str, cache_key: str, ttl: int = 300) -> Optional[List[Dict]]:
    """Get recommendations from cache if available"""
    try:
        # Simple in-memory cache for now
        if hasattr(get_cached_recommendations, '_cache'):
            cache_data = get_cached_recommendations._cache.get(f"{user_id}:{cache_key}")
            if cache_data and time.time() - cache_data['timestamp'] < ttl:
                logger.info(f"⚡ Cache HIT for user {user_id}")
                return cache_data['data']
        return None
    except Exception as e:
        logger.warning(f"Cache error: {e}")
        return None

def set_cached_recommendations(user_id: str, cache_key: str, recommendations: List[Dict], ttl: int = 300):
    """Cache recommendations with TTL"""
    try:
        if not hasattr(set_cached_recommendations, '_cache'):
            set_cached_recommendations._cache = {}
        
        cache_key_full = f"{user_id}:{cache_key}"
        set_cached_recommendations._cache[cache_key_full] = {
            'data': recommendations,
            'timestamp': time.time(),
            'ttl': ttl
        }
        logger.info(f"💾 Cached recommendations for user {user_id}")
    except Exception as e:
        logger.warning(f"Cache error: {e}")

# Import time module for cache TTL
import time

class RecommendationsService:
    """Advanced recommendations using vector similarity and collaborative filtering"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_service = VectorService(db)
    
    def get_vector_recommendations(self, user_id: UUID, limit: int = 10,
                                 category_filter: Optional[str] = None,
                                 brand_filter: Optional[UUID] = None,
                                 weights: Optional[Dict[str, float]] = None,
                                 use_time_weighting: bool = True,
                                 diversity_boost: float = 0.3,
                                 randomness_factor: float = 0.2) -> List[Dict[str, Any]]:
        """Get vector-based recommendations for a user with diversity and variety"""
        try:
            logger.info(f"🎯 Getting vector recommendations for user {user_id}")
            
            # OPTIMIZATION: Check cache first
            cache_key = f"vector_rec_{user_id}_{limit}_{category_filter}_{brand_filter}_{hash(str(weights))}"
            cached_result = get_cached_recommendations(str(user_id), cache_key, ttl=180)  # 3 min cache
            if cached_result:
                logger.info(f"⚡ Cache HIT for user {user_id}")
                return cached_result
            
            logger.info(f"❄️ Cache MISS for user {user_id}")
            
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"❌ User {user_id} not found")
                return []
            
            # OPTIMIZATION: Single query to get user's swipe history with product data
            user_swipes_with_products = self.db.query(
                Swipe, Product.category, Product.brand_id
            ).join(
                Product, Swipe.product_id == Product.id
            ).filter(
                Swipe.user_id == user_id
            ).all()
            
            liked_products = {s.Swipe.product_id for s in user_swipes_with_products if s.Swipe.action == "right"}
            disliked_products = {s.Swipe.product_id for s in user_swipes_with_products if s.Swipe.action == "left"}
            
            # OPTIMIZATION: Use FAISS for fast similarity search if available
            if hasattr(self.vector_service, 'indexes') and self.vector_service.indexes:
                logger.info(f"🚀 Using FAISS indexes for fast similarity search")
                recommendations = self._get_faiss_recommendations(
                    user_id, limit, category_filter, brand_filter, 
                    liked_products, disliked_products, weights
                )
            else:
                logger.info(f"🐌 Falling back to brute force similarity search")
                recommendations = self._get_brute_force_recommendations(
                    user_id, limit, category_filter, brand_filter, 
                    liked_products, disliked_products, weights, use_time_weighting
                )
            
            # Cache the results
            if recommendations:
                set_cached_recommendations(str(user_id), cache_key, recommendations, ttl=180)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Failed to get vector recommendations for user {user_id}: {e}")
            return []
    
    def _get_faiss_recommendations(self, user_id: UUID, limit: int, 
                                  category_filter: Optional[str], brand_filter: Optional[UUID],
                                  liked_products: set, disliked_products: set,
                                  weights: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Get recommendations using FAISS indexes for fast similarity search"""
        try:
            # Get user preference vectors
            preference_vectors = self.vector_service.get_user_preference_vectors_cached(user_id)
            if not preference_vectors:
                logger.warning(f"⚠️ No preference vectors available for user {user_id}")
                logger.info(f"🎲 Providing random products as fallback for new user")
                
                # Fallback: Get random products for new users
                random_products = self._get_random_products_fallback(user_id, limit, category_filter, brand_filter)
                if random_products:
                    logger.info(f"🎲 Fallback: Returning {len(random_products)} random products")
                    return random_products
                else:
                    logger.warning(f"⚠️ Fallback also failed - no products available")
                    return []
            
            # Use FAISS for fast similarity search
            exclude_ids = liked_products | disliked_products
            logger.info(f"🚫 Excluding {len(exclude_ids)} swiped products (liked: {len(liked_products)}, disliked: {len(disliked_products)})")
            
            similar_products = self.vector_service.find_similar_products_faiss(
                query_vectors=preference_vectors,
                limit=limit * 2,  # Get more candidates for diversity
                exclude_ids=exclude_ids,
                category_filter=category_filter,
                brand_filter=brand_filter
            )
            
            # Format results
            recommendations = []
            for product, similarity_score in similar_products[:limit]:
                recommendation = {
                    'product': product,
                    'score': similarity_score,
                    'reason': f"Similar to your preferences (FAISS score: {similarity_score:.4f})",
                    'vector_metadata': {
                        'method': 'faiss_index',
                        'has_combined_vector': bool(product.combined_vector),
                        'cached': True
                    }
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ FAISS recommendations failed: {e}")
            return []
    
    def _get_brute_force_recommendations(self, user_id: UUID, limit: int,
                                        category_filter: Optional[str], brand_filter: Optional[UUID],
                                        liked_products: set, disliked_products: set,
                                        weights: Optional[Dict[str, float]], use_time_weighting: bool) -> List[Dict[str, Any]]:
        """Fallback to brute force similarity search (slower but more reliable)"""
        try:
            # Get user's preference vectors (time-weighted if enabled)
            if use_time_weighting:
                preference_vectors = self.vector_service.get_user_preference_vectors_weighted(user_id)
            else:
                preference_vectors = self.vector_service.get_user_preference_vectors(user_id)
            
            if not preference_vectors:
                logger.warning(f"⚠️ No preference vectors available for user {user_id}, falling back to basic recommendations")
                return self._get_basic_recommendations(user_id, limit, category_filter, brand_filter)
            
            # OPTIMIZATION: Single query with all filters applied
            query = self.db.query(Product).filter(
                Product.combined_vector.isnot(None),
                ~Product.id.in_(liked_products | disliked_products)
            )
            
            # Apply filters
            if category_filter:
                query = query.filter(Product.category == category_filter)
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            # OPTIMIZATION: Limit initial query to reduce memory usage
            candidate_products = query.limit(500).all()  # Reduced from 1000 for better performance
            
            if not candidate_products:
                logger.warning("❌ No candidate products found")
                return []
            
            # OPTIMIZATION: Use only combined vectors for faster processing
            products_with_vectors = []
            for product in candidate_products:
                if product.combined_vector:
                    products_with_vectors.append({
                        'product': product,
                        'combined_vector': product.combined_vector
                    })
            
            # Find similar products using preference vectors
            similar_products = self.vector_service.vectorizer.find_similar_products(
                query_vectors=preference_vectors,
                product_vectors=products_with_vectors,
                limit=min(limit * 2, len(products_with_vectors)),
                weights=weights
            )
            
            # Apply diversity and variety improvements
            final_recommendations = self._apply_diversity_and_variety(
                similar_products=similar_products,
                user_id=user_id,
                limit=limit,
                diversity_boost=0.2,  # Reduced for better performance
                randomness_factor=0.1,  # Reduced for better performance
                db=self.db,
                user_swipes_with_products=user_swipes_with_products
            )
            
            # Format results
            recommendations = []
            for i, (product, similarity_score) in enumerate(final_recommendations):
                recommendation = {
                    'product': product,
                    'score': similarity_score,
                    'reason': self._generate_recommendation_reason(product, similarity_score),
                    'vector_metadata': {
                        'method': 'brute_force',
                        'has_combined_vector': bool(product.combined_vector),
                        'time_weighted': use_time_weighting,
                        'diversity_boosted': True
                    }
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Brute force recommendations failed: {e}")
            return []
    
    def get_similar_products(self, product_id: UUID, user_id: Optional[UUID] = None,
                           limit: int = 10, category_filter: Optional[str] = None,
                           brand_filter: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get similar products based on a specific product"""
        try:
            similar_products = self.vector_service.find_similar_products(
                product_id=product_id,
                limit=limit,
                exclude_swiped_by=user_id,
                category_filter=category_filter,
                brand_filter=brand_filter
            )
            
            # Format results
            recommendations = []
            for product, similarity_score in similar_products:
                recommendation = {
                    'product': product,
                    'score': similarity_score,
                    'reason': f"Similar to {product.name}",
                    'vector_metadata': {
                        'has_image_vector': bool(product.image_vector),
                        'has_text_vector': bool(product.text_vector),
                        'has_combined_vector': bool(product.combined_vector)
                    }
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get similar products for {product_id}: {e}")
            return []
    
    def search_by_text(self, text_query: str, user_id: Optional[UUID] = None,
                      limit: int = 10, category_filter: Optional[str] = None,
                      brand_filter: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Search products using text similarity"""
        try:
            similar_products = self.vector_service.find_similar_by_text(
                text_query=text_query,
                limit=limit,
                exclude_swiped_by=user_id,
                category_filter=category_filter,
                brand_filter=brand_filter
            )
            
            # Format results
            recommendations = []
            for product, similarity_score in similar_products:
                recommendation = {
                    'product': product,
                    'score': similarity_score,
                    'reason': f"Matches search: '{text_query}'",
                    'vector_metadata': {
                        'has_image_vector': bool(product.image_vector),
                        'has_text_vector': bool(product.text_vector),
                        'has_combined_vector': bool(product.combined_vector)
                    }
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to search products by text: {e}")
            return []
    
    def get_hybrid_recommendations(self, user_id: UUID, search_query: Optional[str] = None,
                                 limit: int = 10, category_filter: Optional[str] = None,
                                 brand_filter: Optional[UUID] = None,
                                 vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """Get hybrid recommendations combining vector similarity with search"""
        try:
            recommendations = []
            
            # Get vector-based recommendations
            if vector_weight > 0:
                vector_recs = self.get_vector_recommendations(
                    user_id=user_id,
                    limit=int(limit * vector_weight),
                    category_filter=category_filter,
                    brand_filter=brand_filter
                )
                recommendations.extend(vector_recs)
            
            # Get search-based recommendations if query provided
            if search_query and vector_weight < 1.0:
                search_recs = self.search_by_text(
                    text_query=search_query,
                    user_id=user_id,
                    limit=int(limit * (1 - vector_weight)),
                    category_filter=category_filter,
                    brand_filter=brand_filter
                )
                recommendations.extend(search_recs)
            
            # Remove duplicates and sort by score
            seen_products = set()
            unique_recommendations = []
            
            for rec in recommendations:
                product_id = rec['product'].id
                if product_id not in seen_products:
                    seen_products.add(product_id)
                    unique_recommendations.append(rec)
            
            # Sort by score and return top results
            unique_recommendations.sort(key=lambda x: x['score'], reverse=True)
            return unique_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get hybrid recommendations for user {user_id}: {e}")
            return []
    
    def get_recommendation_status(self, user_id: UUID) -> Dict[str, Any]:
        """Get recommendation status and quality metrics for a user"""
        try:
            # Get user's swipe statistics
            total_swipes = self.db.query(Swipe).filter(Swipe.user_id == user_id).count()
            liked_swipes = self.db.query(Swipe).filter(
                Swipe.user_id == user_id,
                Swipe.action == "right"
            ).count()
            
            # Get vectorization status
            vector_status = self.vector_service.get_vectorization_status()
            
            # Get user's preference vectors
            preference_vectors = self.vector_service.get_user_preference_vectors(user_id)
            
            # Calculate recommendation quality
            can_use_vectors = bool(preference_vectors)
            recommendation_quality = "excellent" if liked_swipes >= 10 else "good" if liked_swipes >= 5 else "basic" if liked_swipes > 0 else "none"
            
            return {
                'user_id': str(user_id),
                'swipe_stats': {
                    'total_swipes': total_swipes,
                    'liked_swipes': liked_swipes,
                    'like_percentage': round((liked_swipes / total_swipes) * 100, 2) if total_swipes > 0 else 0
                },
                'vector_status': vector_status,
                'recommendation_quality': {
                    'can_use_vectors': can_use_vectors,
                    'quality_level': recommendation_quality,
                    'preference_vectors_available': bool(preference_vectors),
                    'recommended_weights': {
                        'image_weight': 0.6 if can_use_vectors else 0.0,
                        'text_weight': 0.4 if can_use_vectors else 0.0
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get recommendation status for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _get_basic_recommendations(self, user_id: UUID, limit: int,
                                 category_filter: Optional[str] = None,
                                 brand_filter: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Fallback to basic recommendations when vectors are not available"""
        try:
            # Get swiped product IDs
            swiped_ids = set(r[0] for r in self.db.query(Swipe.product_id).filter(
                Swipe.user_id == user_id
            ).all())
            
            # Build query
            query = self.db.query(Product).filter(~Product.id.in_(swiped_ids))
            
            # Apply filters
            if category_filter:
                query = query.filter(Product.category == category_filter)
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            # Get random products
            products = query.order_by(func.random()).limit(limit).all()
            
            # Format results
            recommendations = []
            for product in products:
                recommendation = {
                    'product': product,
                    'score': 0.5,  # Default score for basic recommendations
                    'reason': 'Random recommendation (no vector data available)',
                    'vector_metadata': {
                        'has_image_vector': bool(product.image_vector),
                        'has_text_vector': bool(product.text_vector),
                        'has_combined_vector': bool(product.combined_vector)
                    }
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get basic recommendations for user {user_id}: {e}")
            return []
    
    def _generate_recommendation_reason(self, product: Product, similarity_score: float) -> str:
        """Generate a human-readable reason for the recommendation"""
        if similarity_score >= 0.8:
            return f"Very similar to products you've liked ({(similarity_score * 100):.0f}% match)"
        elif similarity_score >= 0.6:
            return f"Similar to your preferences ({(similarity_score * 100):.0f}% match)"
        elif similarity_score >= 0.4:
            return f"Somewhat similar to your style ({(similarity_score * 100):.0f}% match)"
        else:
            return f"Based on your preferences ({(similarity_score * 100):.0f}% match)" 
    
    def get_collaborative_recommendations(self, user_id: UUID, limit: int = 10,
                                        category_filter: Optional[str] = None,
                                        brand_filter: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get collaborative filtering recommendations based on similar users"""
        try:
            logger.info(f"🎯 Getting collaborative recommendations for user {user_id}")
            
            # Get user's swipe history
            user_swipes = self.db.query(Swipe).filter(Swipe.user_id == user_id).all()
            user_likes = {s.product_id for s in user_swipes if s.action == "right"}
            user_dislikes = {s.product_id for s in user_swipes if s.action == "left"}
            
            if not user_likes:
                logger.info(f"User {user_id} has no likes, skipping collaborative filtering")
                return []
            
            # Find similar users (users who liked similar products)
            similar_users = self._find_similar_users(user_id, user_likes, min_similarity=0.3)
            
            if not similar_users:
                logger.info(f"No similar users found for user {user_id}")
                return []
            
            # Get products liked by similar users
            similar_user_ids = [u['user_id'] for u in similar_users]
            similar_user_likes = self.db.query(Swipe.product_id).filter(
                Swipe.user_id.in_(similar_user_ids),
                Swipe.action == "right"
            ).all()
            
            # Count product popularity among similar users
            product_scores = defaultdict(float)
            for product_id, in similar_user_likes:
                if product_id not in user_likes and product_id not in user_dislikes:
                    # Weight by user similarity
                    for similar_user in similar_users:
                        if similar_user['user_id'] in similar_user_ids:
                            product_scores[product_id] += similar_user['similarity']
            
            # Get top scoring products
            top_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:limit*2]
            
            # Build query for products
            product_ids = [p[0] for p in top_products]
            query = self.db.query(Product).filter(Product.id.in_(product_ids))
            
            # Apply filters
            if category_filter:
                query = query.filter(Product.category == category_filter)
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            products = query.all()
            
            # Format results
            recommendations = []
            for product in products[:limit]:
                score = product_scores.get(product.id, 0)
                recommendation = {
                    'product': product,
                    'score': score,
                    'reason': f"Liked by {len([u for u in similar_users if u['user_id'] in similar_user_ids])} similar users",
                    'vector_metadata': {
                        'has_image_vector': bool(product.image_vector),
                        'has_text_vector': bool(product.text_vector),
                        'has_combined_vector': bool(product.combined_vector),
                        'collaborative_score': score
                    }
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get collaborative recommendations for user {user_id}: {e}")
            return []
    
    def _find_similar_users(self, user_id: UUID, user_likes: set, min_similarity: float = 0.3) -> List[Dict[str, Any]]:
        """Find users with similar preferences using Jaccard similarity"""
        try:
            # Get all users who have liked products
            all_users = self.db.query(Swipe.user_id).filter(
                Swipe.action == "right"
            ).distinct().all()
            
            similar_users = []
            for other_user_id, in all_users:
                if other_user_id == user_id:
                    continue
                
                # Get other user's likes
                other_likes = set(r[0] for r in self.db.query(Swipe.product_id).filter(
                    Swipe.user_id == other_user_id,
                    Swipe.action == "right"
                ).all())
                
                if not other_likes:
                    continue
                
                # Calculate Jaccard similarity
                intersection = len(user_likes & other_likes)
                union = len(user_likes | other_likes)
                
                if union > 0:
                    similarity = intersection / union
                    if similarity >= min_similarity:
                        similar_users.append({
                            'user_id': other_user_id,
                            'similarity': similarity,
                            'common_likes': intersection
                        })
            
            # Sort by similarity
            similar_users.sort(key=lambda x: x['similarity'], reverse=True)
            return similar_users[:10]  # Limit to top 20 similar users
            
        except Exception as e:
            logger.error(f"Failed to find similar users for {user_id}: {e}")
            return []

    def get_hybrid_recommendations_improved(self, user_id: UUID, 
                                          vector_weight: float = 0.4,
                                          collaborative_weight: float = 0.3,
                                          content_weight: float = 0.3,
                                          limit: int = 10,
                                          category_filter: Optional[str] = None,
                                          brand_filter: Optional[UUID] = None,
                                          use_time_weighting: bool = True) -> List[Dict[str, Any]]:
        """Get improved hybrid recommendations combining multiple approaches"""
        try:
            logger.info(f"🎯 Getting hybrid recommendations for user {user_id}")
            logger.info(f"⚖️ Weights: vector={vector_weight}, collaborative={collaborative_weight}, content={content_weight}")
            logger.info(f"⏰ Time weighting: {use_time_weighting}")
            
            all_recommendations = []
            
            # Get vector-based recommendations (with time weighting)
            if vector_weight > 0:
                vector_recs = self.get_vector_recommendations(
                    user_id=user_id,
                    limit=int(limit * 2),  # Get more to allow for filtering
                    category_filter=category_filter,
                    brand_filter=brand_filter,
                    use_time_weighting=use_time_weighting
                )
                for rec in vector_recs:
                    rec['final_score'] = rec['score'] * vector_weight
                    rec['method'] = 'vector'
                all_recommendations.extend(vector_recs)
                logger.info(f"📊 Added {len(vector_recs)} vector-based recommendations")
            
            # Get collaborative filtering recommendations
            if collaborative_weight > 0:
                collab_recs = self.get_collaborative_recommendations(
                    user_id=user_id,
                    limit=int(limit * 2),
                    category_filter=category_filter,
                    brand_filter=brand_filter
                )
                for rec in collab_recs:
                    rec['final_score'] = rec['score'] * collaborative_weight
                    rec['method'] = 'collaborative'
                all_recommendations.extend(collab_recs)
                logger.info(f"👥 Added {len(collab_recs)} collaborative recommendations")
            
            # Get content-based recommendations (basic category/brand matching)
            if content_weight > 0:
                content_recs = self._get_content_based_recommendations(
                    user_id=user_id,
                    limit=int(limit * 2),
                    category_filter=category_filter,
                    brand_filter=brand_filter
                )
                for rec in content_recs:
                    rec['final_score'] = rec['score'] * content_weight
                    rec['method'] = 'content'
                all_recommendations.extend(content_recs)
                logger.info(f"🏷️ Added {len(content_recs)} content-based recommendations")
            
            # Combine and deduplicate recommendations
            product_scores = defaultdict(list)
            for rec in all_recommendations:
                product_id = rec['product'].id
                product_scores[product_id].append(rec)
            
            logger.info(f"🔄 Combining {len(all_recommendations)} recommendations into {len(product_scores)} unique products")
            
            # Calculate final scores and select best recommendations
            final_recommendations = []
            for product_id, recs in product_scores.items():
                # Average scores from different methods
                avg_score = sum(r['final_score'] for r in recs) / len(recs)
                best_rec = max(recs, key=lambda x: x['final_score'])
                
                # Create method description
                method_descriptions = []
                for rec in recs:
                    if rec['method'] == 'vector':
                        method_desc = f"vector{' (time-weighted)' if rec['vector_metadata'].get('time_weighted') else ''}"
                    elif rec['method'] == 'collaborative':
                        method_desc = f"collaborative (score: {rec['score']:.3f})"
                    else:
                        method_desc = f"content (score: {rec['score']:.3f})"
                    method_descriptions.append(method_desc)
                
                final_rec = {
                    'product': best_rec['product'],
                    'score': avg_score,
                    'final_score': avg_score,
                    'reason': f"Combined from {len(recs)} methods: {', '.join(method_descriptions)}",
                    'vector_metadata': best_rec['vector_metadata'],
                    'methods_used': [r['method'] for r in recs],
                    'method_scores': {r['method']: r['final_score'] for r in recs},
                    'hybrid_metadata': {
                        'total_methods': len(recs),
                        'time_weighted': use_time_weighting,
                        'vector_weight': vector_weight,
                        'collaborative_weight': collaborative_weight,
                        'content_weight': content_weight
                    }
                }
                final_recommendations.append(final_rec)
            
            # Sort by final score and return top results
            final_recommendations.sort(key=lambda x: x['final_score'], reverse=True)
            logger.info(f"✅ Returning top {min(limit, len(final_recommendations))} hybrid recommendations")
            return final_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get hybrid recommendations for user {user_id}: {e}")
            return []
    
    def _get_content_based_recommendations(self, user_id: UUID, limit: int,
                                         category_filter: Optional[str] = None,
                                         brand_filter: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get content-based recommendations using category and brand preferences"""
        try:
            # Get user's preferences
            user_preferences = self.db.query(
                Swipe.action,
                Product.category,
                Product.brand_id
            ).join(
                Product, Swipe.product_id == Product.id
            ).filter(
                Swipe.user_id == user_id
            ).all()
            
            # Extract preferences
            liked_categories = [p.category for p in user_preferences if p.action == "right" and p.category]
            disliked_categories = [p.category for p in user_preferences if p.action == "left" and p.category]
            liked_brands = [p.brand_id for p in user_preferences if p.action == "right" and p.brand_id]
            disliked_brands = [p.brand_id for p in user_preferences if p.action == "left" and p.brand_id]
            
            # Get swiped product IDs
            swiped_ids = set(r[0] for r in self.db.query(Swipe.product_id).filter(
                Swipe.user_id == user_id
            ).all())
            
            # Build query
            query = self.db.query(Product).filter(~Product.id.in_(swiped_ids))
            
            # Apply filters
            if category_filter:
                query = query.filter(Product.category == category_filter)
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            # Score products based on preferences using correct SQLAlchemy syntax
            scored_products = query.add_columns(
                case(
                    (Product.category.in_(liked_categories), 3),
                    (Product.brand_id.in_(liked_brands), 2),
                    else_=1
                ).label('score')
            ).filter(
                ~Product.category.in_(disliked_categories) if disliked_categories else True,
                ~Product.brand_id.in_(disliked_brands) if disliked_brands else True
            ).order_by(
                case(
                    (Product.category.in_(liked_categories), 3),
                    (Product.brand_id.in_(liked_brands), 2),
                    else_=1
                ).desc(),
                func.random()
            ).limit(limit).all()
            
            # Format results
            recommendations = []
            for product, score in scored_products:
                recommendation = {
                    'product': product,
                    'score': float(score) / 3.0,  # Normalize to 0-1
                    'reason': f"Matches your preferences (category: {product.category}, brand: {product.brand_id})",
                    'vector_metadata': {
                        'has_image_vector': bool(product.image_vector),
                        'has_text_vector': bool(product.text_vector),
                        'has_combined_vector': bool(product.combined_vector)
                    }
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get content-based recommendations for user {user_id}: {e}")
            return [] 
    
    def _apply_diversity_and_variety(self, similar_products: List[Tuple[Product, float]], 
                                   user_id: UUID, limit: int, diversity_boost: float,
                                   randomness_factor: float, db: Session, user_swipes_with_products: List[Tuple[Swipe, Product.category, Product.brand_id]]) -> List[Tuple[Product, float]]:
        """Apply diversity boosting and variety to recommendations"""
        try:
            if not similar_products:
                return []
            
            # Get user's recent preferences for diversity analysis
            recent_swipes = db.query(Swipe).filter(
                Swipe.user_id == user_id
            ).order_by(Swipe.created_at.desc()).limit(20).all()
            
            # Analyze user's recent preferences
            recent_categories = [s.product.category for s in recent_swipes if s.product.category]
            recent_brands = [s.product.brand_id for s in recent_swipes if s.product.brand_id]
            
            # Count recent preferences
            category_counts = {}
            brand_counts = {}
            for swipe in recent_swipes:
                if swipe.product.category:
                    category_counts[swipe.product.category] = category_counts.get(swipe.product.category, 0) + 1
                if swipe.product.brand_id:
                    brand_counts[swipe.product.brand_id] = brand_counts.get(swipe.product.brand_id, 0) + 1
            
            logger.info(f"📊 Recent preferences: {len(category_counts)} categories, {len(brand_counts)} brands")
            
            # Score products with diversity and variety factors
            scored_products = []
            for product, base_score in similar_products:
                # Start with base similarity score
                final_score = base_score
                
                # Diversity boost: prefer different categories/brands
                diversity_score = 0
                if product.category and product.category in category_counts:
                    # Penalize over-represented categories
                    category_frequency = category_counts[product.category] / len(recent_swipes)
                    diversity_score -= category_frequency * 0.5
                
                if product.brand_id and product.brand_id in brand_counts:
                    # Penalize over-represented brands
                    brand_frequency = brand_counts[product.brand_id] / len(recent_swipes)
                    diversity_score -= brand_frequency * 0.3
                
                # Boost underrepresented categories/brands
                if product.category and product.category not in category_counts:
                    diversity_score += 0.2
                if product.brand_id and product.brand_id not in brand_counts:
                    diversity_score += 0.1
                
                # Apply diversity boost
                final_score += diversity_score * diversity_boost
                
                # Add randomness factor
                import random
                random_factor = (random.random() - 0.5) * randomness_factor
                final_score += random_factor
                
                # Ensure score stays in reasonable range
                final_score = max(0.0, min(1.0, final_score))
                
                scored_products.append((product, final_score))
                
                logger.debug(f"   {product.name}: base={base_score:.3f}, diversity={diversity_score:.3f}, final={final_score:.3f}")
            
            # Sort by final score and return top results
            scored_products.sort(key=lambda x: x[1], reverse=True)
            
            # Ensure we don't have too many from the same category/brand
            final_selection = []
            selected_categories = set()
            selected_brands = set()
            
            for product, score in scored_products:
                # Check if we already have enough from this category/brand
                category_limit_reached = (product.category in selected_categories and 
                                        len([p for p, _ in final_selection if p.category == product.category]) >= 2)
                brand_limit_reached = (product.brand_id in selected_brands and 
                                     len([p for p, _ in final_selection if p.brand_id == product.brand_id]) >= 2)
                
                if not category_limit_reached and not brand_limit_reached:
                    final_selection.append((product, score))
                    if product.category:
                        selected_categories.add(product.category)
                    if product.brand_id:
                        selected_brands.add(product.brand_id)
                
                if len(final_selection) >= limit:
                    break
            
            # If we don't have enough, add remaining products
            if len(final_selection) < limit:
                remaining = [p for p in scored_products if p not in final_selection]
                final_selection.extend(remaining[:limit - len(final_selection)])
            
            logger.info(f"🎯 Final selection: {len(final_selection)} products with diversity and variety")
            return final_selection[:limit]
            
        except Exception as e:
            logger.error(f"Failed to apply diversity and variety: {e}")
            return similar_products[:limit]
    
    def _get_random_products_fallback(self, user_id: UUID, limit: int, 
                                    category_filter: Optional[str], 
                                    brand_filter: Optional[UUID]) -> List[Dict[str, Any]]:
        """Get random products as fallback when user has no preference vectors"""
        try:
            logger.info(f"🎲 Getting random products fallback for user {user_id}")
            
            # Build query for random products
            query = self.db.query(Product).filter(
                Product.combined_vector.isnot(None)  # Must have vectors for consistency
            )
            
            # Apply filters if specified
            if category_filter:
                query = query.filter(Product.category == category_filter)
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            # Get total count for random selection
            total_products = query.count()
            if total_products == 0:
                logger.warning(f"⚠️ No products available for random fallback")
                return []
            
            # Get random products using OFFSET and LIMIT
            import random
            offset = random.randint(0, max(0, total_products - limit))
            
            random_products = query.offset(offset).limit(limit * 2).all()  # Get more to allow for filtering
            
            if not random_products:
                logger.warning(f"⚠️ Random query returned no products")
                return []
            
            # Shuffle and select random products
            random.shuffle(random_products)
            selected_products = random_products[:limit]
            
            # Format as recommendations with random scores
            recommendations = []
            for i, product in enumerate(selected_products):
                # Generate a random but reasonable similarity score
                random_score = 0.5 + (random.random() * 0.3)  # Score between 0.5-0.8
                
                recommendation = {
                    'product': product,
                    'score': random_score,
                    'reason': f"Random product to get you started!",
                    'vector_metadata': {
                        'method': 'random_fallback',
                        'has_combined_vector': bool(product.combined_vector),
                        'fallback': True
                    }
                }
                recommendations.append(recommendation)
            
            logger.info(f"🎲 Random fallback: Generated {len(recommendations)} random products")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Random products fallback failed: {e}")
            return [] 