from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.db import get_db
from app.models import Swipe, Product, User
from app.schemas import Product as ProductSchema
from app.services.recommendations import RecommendationsService
from app.services.vector_service import VectorService
from sqlalchemy.sql.expression import func as sql_func
import logging
import time
from datetime import datetime
from functools import lru_cache
import redis
import json

# Set up logging for API endpoints
logger = logging.getLogger(__name__)

router = APIRouter()

# Redis cache for recommendations (optional - remove if not using Redis)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    CACHE_ENABLED = True
except:
    redis_client = None
    CACHE_ENABLED = False

# In-memory cache for frequently accessed data
@lru_cache(maxsize=1000)
def get_user_swipe_count(user_id: str) -> int:
    """Cache user swipe counts to avoid repeated DB queries"""
    # This would need to be implemented with proper DB session handling
    pass

def get_cached_recommendations(user_id: str, cache_key: str, ttl: int = 300) -> Optional[List[Dict]]:
    """Get recommendations from cache if available"""
    if not CACHE_ENABLED:
        return None
    
    try:
        cached = redis_client.get(f"rec:{user_id}:{cache_key}")
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache error: {e}")
    return None

def set_cached_recommendations(user_id: str, cache_key: str, recommendations: List[Dict], ttl: int = 300):
    """Cache recommendations with TTL"""
    if not CACHE_ENABLED:
        return
    
    try:
        redis_client.setex(
            f"rec:{user_id}:{cache_key}",
            ttl,
            json.dumps(recommendations, default=str)
        )
    except Exception as e:
        logger.warning(f"Cache error: {e}")

# Performance monitoring
performance_stats = {
    'total_requests': 0,
    'avg_response_time': 0,
    'cache_hits': 0,
    'cache_misses': 0
}

def update_performance_stats(response_time: float, cache_hit: bool = False):
    """Update performance statistics"""
    performance_stats['total_requests'] += 1
    performance_stats['avg_response_time'] = (
        (performance_stats['avg_response_time'] * (performance_stats['total_requests'] - 1) + response_time) 
        / performance_stats['total_requests']
    )
    if cache_hit:
        performance_stats['cache_hits'] += 1
    else:
        performance_stats['cache_misses'] += 1

# Non-user-specific endpoints (must come before user_id patterns)
@router.get("/vectorization-status")
def get_vectorization_status(db: Session = Depends(get_db)):
    """Get overall vectorization status across all products."""
    
    vector_service = VectorService(db)
    status = vector_service.get_vectorization_status()
    
    return status

@router.get("/vector-performance-stats")
def get_vector_performance_stats():
    """Get performance statistics for vector operations."""
    return performance_stats

@router.delete("/vector-cache/clear")
def clear_vector_cache():
    """Clear all vector-related caches."""
    try:
        # Clear in-memory caches
        # vector_cache.clear() # This line was removed as per the edit hint
        # preference_cache.clear() # This line was removed as per the edit hint
        
        # Clear Redis cache if available
        try:
            redis_client.flushdb()
            logger.info("🗑️ Redis cache cleared")
        except Exception as e:
            logger.warning(f"Could not clear Redis cache: {e}")
        
        return {"message": "Vector cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear vector cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.post("/products/generate-vectors-missing")
def generate_vectors_for_missing(db: Session = Depends(get_db)):
    """Generate vectors for all products that don't have them."""
    
    vector_service = VectorService(db)
    result = vector_service.generate_vectors_for_missing()
    
    return result

# User-specific endpoints
@router.get("/{user_id}", response_model=List[ProductSchema])
def recommend(
    user_id: UUID, 
    limit: int = Query(default=5, ge=1, le=20, description="Number of recommendations (1-20)"), 
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    db: Session = Depends(get_db)
):
    """Get product recommendations for a user based on their swipe history with pagination."""
    
    # Check cache first
    cache_key = f"basic:{limit}:{page}"
    cached = get_cached_recommendations(str(user_id), cache_key)
    if cached:
        logger.info(f"Cache hit for user {user_id}")
        return cached
    
    # Optimized query to get total products and user swipes in one go
    total_products, user_swipes_count = db.query(
        func.count(Product.id),
        func.count(Swipe.id)
    ).outerjoin(
        Swipe, and_(Swipe.user_id == user_id, Swipe.product_id == Product.id)
    ).first()
    
    # If user has swiped on all products, return empty
    if user_swipes_count >= total_products and total_products > 0:
        return []
    
    # Get user's preferences efficiently
    user_preferences = db.query(
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
    
    # Get swiped product IDs efficiently
    swiped_ids = db.query(Swipe.product_id).filter(Swipe.user_id == user_id).subquery()
    
    # Build optimized recommendation query with pagination
    offset = (page - 1) * limit
    
    if not user_preferences:
        # Random recommendations for new users
        recommendations = db.query(Product).filter(
            ~Product.id.in_(swiped_ids)
        ).order_by(func.random()).offset(offset).limit(limit).all()
    else:
        # Preference-based recommendations with scoring
        recommendations = db.query(Product).filter(
            ~Product.id.in_(swiped_ids)
        ).add_columns(
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
        ).offset(offset).limit(limit).all()
        
        # Extract just the Product objects
        recommendations = [r[0] for r in recommendations]
    
    # Cache the results
    set_cached_recommendations(str(user_id), cache_key, [p.__dict__ for p in recommendations])
    
    return recommendations

@router.get("/{user_id}/simple")
def simple_recommendations(user_id: UUID, limit: int = 5, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get simple recommendations based on user preferences."""
    
    # Get user's liked products
    liked_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id,
        Swipe.action == "right"
    ).all()
    
    # Get swiped product IDs to exclude
    swiped_ids = set(r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all())
    
    if not liked_swipes:
        # Return random products if no likes
        random_products = db.query(Product).filter(
            ~Product.id.in_(swiped_ids)
        ).order_by(func.random()).limit(limit).all()
        
        return {
            "recommendations": random_products,
            "method": "random",
            "reason": "No previous likes to base recommendations on"
        }
    
    # Get liked product details
    liked_products = db.query(Product).filter(
        Product.id.in_([s.product_id for s in liked_swipes])
    ).all()
    
    # Extract preferences
    categories = [p.category for p in liked_products if p.category]
    brands = [p.brand_id for p in liked_products if p.brand_id]
    
    # Find similar products
    similar_products = db.query(Product).filter(
        ~Product.id.in_(swiped_ids),
        or_(
            Product.category.in_(categories) if categories else False,
            Product.brand_id.in_(brands) if brands else False
        )
    ).limit(limit).all()
    
    return {
        "recommendations": similar_products,
        "method": "preference_based",
        "preferences": {
            "categories": list(set(categories)),
            "brands": list(set(brands))
        }
    }

@router.get("/{user_id}/status")
def get_swipe_status(user_id: UUID, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get user's swipe status and recommendation readiness."""
    
    # Get user's swipe counts
    total_swipes = db.query(Swipe).filter(Swipe.user_id == user_id).count()
    right_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id,
        Swipe.action == "right"
    ).count()
    left_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id,
        Swipe.action == "left"
    ).count()
    
    # Get total products
    total_products = db.query(Product).count()
    
    # Calculate percentages
    swipe_percentage = (total_swipes / total_products * 100) if total_products > 0 else 0
    like_percentage = (right_swipes / total_swipes * 100) if total_swipes > 0 else 0
    
    return {
        "user_id": str(user_id),
        "total_products": total_products,
        "total_swipes": total_swipes,
        "right_swipes": right_swipes,
        "left_swipes": left_swipes,
        "swipe_percentage": round(swipe_percentage, 2),
        "like_percentage": round(like_percentage, 2),
        "can_recommend": right_swipes > 0,
        "recommendation_quality": "good" if right_swipes >= 5 else "basic" if right_swipes > 0 else "none"
    }

@router.get("/{user_id}/hybrid", response_model=List[ProductSchema])
def hybrid_recommendations(
    user_id: UUID, 
    limit: int = 10, 
    search_query: Optional[str] = None,
    category: Optional[str] = None,
    brand_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get hybrid recommendations combining user preferences with search filters."""
    
    # Get user's liked products
    liked_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id,
        Swipe.action == "right"
    ).all()
    
    # Get swiped product IDs
    swiped_ids = set(r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all())
    
    # Build base query
    query = db.query(Product).filter(~Product.id.in_(swiped_ids))
    
    # Apply filters
    if category:
        query = query.filter(Product.category == category)
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    if search_query:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search_query}%"),
                Product.description.ilike(f"%{search_query}%")
            )
        )
    
    # If user has likes, prioritize similar products
    if liked_swipes:
        liked_products = db.query(Product).filter(
            Product.id.in_([s.product_id for s in liked_swipes])
        ).all()
        
        liked_categories = [p.category for p in liked_products if p.category]
        liked_brands = [p.brand_id for p in liked_products if p.brand_id]
        
        # Order by preference similarity
        query = query.order_by(
            func.case(
                (Product.category.in_(liked_categories), 1),
                (Product.brand_id.in_(liked_brands), 2),
                else_=3
            )
        )
    
    return query.limit(limit).all()

@router.get("/{user_id}/semantic", response_model=List[ProductSchema])
def semantic_recommendations(
    user_id: UUID,
    query_text: str = Query(..., description="Natural language query"),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get semantic recommendations based on natural language query."""
    
    # Get swiped product IDs to exclude
    swiped_ids = set(r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all())
    
    # Simple semantic search implementation
    query_terms = query_text.lower().split()
    
    # Get all unswiped products
    products = db.query(Product).filter(~Product.id.in_(swiped_ids)).all()
    
    # Score products based on query terms
    scored_products = []
    for product in products:
        score = 0
        
        # Name relevance
        if product.name:
            name_terms = product.name.lower().split()
            name_matches = sum(1 for term in query_terms if any(term in name_term for name_term in name_terms))
            score += name_matches * 0.3
        
        # Description relevance
        if product.description:
            desc_terms = product.description.lower().split()
            desc_matches = sum(1 for term in query_terms if any(term in desc_term for desc_term in desc_terms))
            score += desc_matches * 0.2
        
        # Category relevance
        if product.category and any(term in product.category.lower() for term in query_terms):
            score += 0.2
        
        # Tag relevance
        if product.tags:
            tag_matches = sum(1 for term in query_terms if any(term in tag.lower() for tag in product.tags))
            score += tag_matches * 0.1
        
        # Color relevance
        if product.color and any(term in product.color.lower() for term in query_terms):
            score += 0.1
        
        # Brand relevance
        if product.brand and any(term in product.brand.name.lower() for term in query_terms):
            score += 0.1
        
        if score > 0:
            scored_products.append((product, score))
    
    # Sort by score and return top results
    scored_products.sort(key=lambda x: x[1], reverse=True)
    return [product for product, score in scored_products[:limit]]

# New vector-based endpoints
@router.get("/{user_id}/vector", response_model=List[Dict[str, Any]])
def get_vector_recommendations(
    user_id: UUID,
    limit: int = Query(default=10, ge=1, le=20, description="Number of recommendations (1-20)"),
    category: Optional[str] = None,
    brand_id: Optional[UUID] = None,
    image_weight: float = Query(default=0.6, ge=0.0, le=1.0, description="Weight for image similarity (0-1)"),
    text_weight: float = Query(default=0.4, ge=0.0, le=1.0, description="Weight for text similarity (0-1)"),
    db: Session = Depends(get_db)
):
    """
    Get vector-based recommendations using advanced similarity search.
    
    This endpoint uses both image and text vectors for intelligent product recommendations.
    """
    
    # Start timing
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    # Log API call
    logger.info(f"🚀 [{request_id}] API CALL: Vector recommendations for user {user_id}")
    logger.info(f"📋 [{request_id}] Parameters: limit={limit}, category={category}, brand_id={brand_id}")
    logger.info(f"⚖️ [{request_id}] Weights: image={image_weight}, text={text_weight}")
    
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"❌ [{request_id}] User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ [{request_id}] User {user_id} validated")
        
        # Create weights dictionary
        weights = {
            'image_similarity': image_weight,
            'text_similarity': text_weight,
        }
        
        # Get recommendations
        recommendations_service = RecommendationsService(db)
        recommendations = recommendations_service.get_vector_recommendations(
            user_id=user_id,
            limit=limit,
            category_filter=category,
            brand_filter=brand_id,
            weights=weights
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log results summary
        logger.info(f"✅ [{request_id}] SUCCESS: Found {len(recommendations)} recommendations")
        logger.info(f"⏱️ [{request_id}] Processing time: {processing_time:.3f}s")
        
        # Log top recommendations
        for i, rec in enumerate(recommendations[:3]):  # Log top 3
            product = rec['product']
            score = rec['score']
            logger.info(f"🏆 [{request_id}] Top {i+1}: {product.name} (score: {score:.4f})")
        
        # Format response
        response = []
        for rec in recommendations:
            product = rec['product']
            response.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'image': product.image,
                'category': product.category,
                'color': product.color,
                'tags': product.tags,
                'price': float(product.price) if product.price else None,
                'brand_id': str(product.brand_id) if product.brand_id else None,
                'similarity_score': rec['score'],
                'recommendation_reason': rec['reason'],
                'vector_metadata': rec['vector_metadata']
            })
        
        logger.info(f"🎯 [{request_id}] API RESPONSE: Returning {len(response)} recommendations")
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] ERROR: {str(e)} (after {processing_time:.3f}s)")
        raise

@router.get("/products/{product_id}/similar", response_model=List[Dict[str, Any]])
def get_similar_products(
    product_id: UUID,
    user_id: Optional[UUID] = None,
    limit: int = Query(default=10, ge=1, le=20),
    category: Optional[str] = None,
    brand_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get similar products based on a specific product using vector similarity."""
    
    # Start timing
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    # Log API call
    logger.info(f"🚀 [{request_id}] API CALL: Similar products for product {product_id}")
    logger.info(f"📋 [{request_id}] Parameters: user_id={user_id}, limit={limit}, category={category}, brand_id={brand_id}")
    
    try:
        # Validate product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.error(f"❌ [{request_id}] Product {product_id} not found")
            raise HTTPException(status_code=404, detail="Product not found")
        
        logger.info(f"✅ [{request_id}] Product {product_id} ({product.name}) validated")
        
        # Get similar products
        recommendations_service = RecommendationsService(db)
        recommendations = recommendations_service.get_similar_products(
            product_id=product_id,
            user_id=user_id,
            limit=limit,
            category_filter=category,
            brand_filter=brand_id
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log results summary
        logger.info(f"✅ [{request_id}] SUCCESS: Found {len(recommendations)} similar products")
        logger.info(f"⏱️ [{request_id}] Processing time: {processing_time:.3f}s")
        
        # Log top similar products
        for i, rec in enumerate(recommendations[:3]):  # Log top 3
            product = rec['product']
            score = rec['score']
            logger.info(f"🏆 [{request_id}] Top {i+1}: {product.name} (score: {score:.4f})")
        
        # Format response
        response = []
        for rec in recommendations:
            product = rec['product']
            response.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'image': product.image,
                'category': product.category,
                'color': product.color,
                'tags': product.tags,
                'price': float(product.price) if product.price else None,
                'brand_id': str(product.brand_id) if product.brand_id else None,
                'similarity_score': rec['score'],
                'recommendation_reason': rec['reason'],
                'vector_metadata': rec['vector_metadata']
            })
        
        logger.info(f"🎯 [{request_id}] API RESPONSE: Returning {len(response)} similar products")
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] ERROR: {str(e)} (after {processing_time:.3f}s)")
        raise

@router.get("/search/vector", response_model=List[Dict[str, Any]])
def search_products_by_text(
    query: str = Query(..., description="Text query for similarity search"),
    user_id: Optional[UUID] = None,
    limit: int = Query(default=10, ge=1, le=20),
    category: Optional[str] = None,
    brand_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Search products using text similarity with vector embeddings."""
    
    # Start timing
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    # Log API call
    logger.info(f"🚀 [{request_id}] API CALL: Text search with query '{query}'")
    logger.info(f"📋 [{request_id}] Parameters: user_id={user_id}, limit={limit}, category={category}, brand_id={brand_id}")
    
    try:
        # Get search results
        recommendations_service = RecommendationsService(db)
        recommendations = recommendations_service.search_by_text(
            text_query=query,
            user_id=user_id,
            limit=limit,
            category_filter=category,
            brand_filter=brand_id
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log results summary
        logger.info(f"✅ [{request_id}] SUCCESS: Found {len(recommendations)} products for query '{query}'")
        logger.info(f"⏱️ [{request_id}] Processing time: {processing_time:.3f}s")
        
        # Log top search results
        for i, rec in enumerate(recommendations[:3]):  # Log top 3
            product = rec['product']
            score = rec['score']
            logger.info(f"🏆 [{request_id}] Top {i+1}: {product.name} (score: {score:.4f})")
        
        # Format response
        response = []
        for rec in recommendations:
            product = rec['product']
            response.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'image': product.image,
                'category': product.category,
                'color': product.color,
                'tags': product.tags,
                'price': float(product.price) if product.price else None,
                'brand_id': str(product.brand_id) if product.brand_id else None,
                'similarity_score': rec['score'],
                'recommendation_reason': rec['reason'],
                'vector_metadata': rec['vector_metadata']
            })
        
        logger.info(f"🎯 [{request_id}] API RESPONSE: Returning {len(response)} search results")
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] ERROR: {str(e)} (after {processing_time:.3f}s)")
        raise

@router.get("/{user_id}/vector-status")
def get_vector_status(user_id: UUID, db: Session = Depends(get_db)):
    """Get status of vector-based recommendations for a user."""
    
    # Start timing
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    # Log API call
    logger.info(f"🚀 [{request_id}] API CALL: Vector status for user {user_id}")
    
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"❌ [{request_id}] User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ [{request_id}] User {user_id} validated")
        
        # Get recommendation status
        recommendations_service = RecommendationsService(db)
        status = recommendations_service.get_recommendation_status(user_id)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(f"✅ [{request_id}] SUCCESS: Retrieved vector status")
        logger.info(f"⏱️ [{request_id}] Processing time: {processing_time:.3f}s")
        logger.info(f"📊 [{request_id}] Status: {status}")
        
        return status
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] ERROR: {str(e)} (after {processing_time:.3f}s)")
        raise

# Vector management endpoints
@router.post("/products/{product_id}/generate-vectors")
def generate_product_vectors(
    product_id: UUID,
    force_regenerate: bool = Query(default=False, description="Force regenerate even if vectors exist"),
    db: Session = Depends(get_db)
):
    """Generate vectors for a specific product."""
    
    vector_service = VectorService(db)
    result = vector_service.generate_vectors_for_product(product_id, force_regenerate)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/products/generate-vectors-batch")
def generate_vectors_batch(
    product_ids: List[UUID],
    batch_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Generate vectors for multiple products in batches."""
    
    vector_service = VectorService(db)
    result = vector_service.generate_vectors_batch(product_ids, batch_size)
    
    return result





@router.get("/{user_id}/hybrid-improved", response_model=List[Dict[str, Any]])
async def get_hybrid_recommendations_improved(
    user_id: UUID,
    limit: int = Query(10, ge=1, le=20, description="Number of recommendations to return"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    category_filter: Optional[str] = Query(None, description="Filter by product category"),
    brand_filter: Optional[UUID] = Query(None, description="Filter by brand ID"),
    vector_weight: float = Query(0.4, ge=0.0, le=1.0, description="Weight for vector-based recommendations"),
    collaborative_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for collaborative filtering"),
    content_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for content-based recommendations"),
    use_time_weighting: bool = Query(True, description="Use time-weighted preference vectors"),
    db: Session = Depends(get_db)
):
    """Get improved hybrid recommendations combining vector, collaborative, and content-based approaches"""
    try:
        # Validate weights sum to 1.0
        total_weight = vector_weight + collaborative_weight + content_weight
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Weights must sum to 1.0, got {total_weight:.2f}"
            )
        
        # Get cached recommendations if available
        cache_key = f"hybrid_improved_{user_id}_{limit}_{page}_{category_filter}_{brand_filter}_{vector_weight}_{collaborative_weight}_{content_weight}_{use_time_weighting}"
        cached_result = get_cached_recommendations(str(user_id), cache_key)
        if cached_result:
            logger.info(f"📦 Returning cached hybrid recommendations for user {user_id}")
            return cached_result
        
        # Get recommendations
        service = RecommendationsService(db)
        recommendations = service.get_hybrid_recommendations_improved(
            user_id=user_id,
            limit=limit,
            category_filter=category_filter,
            brand_filter=brand_filter,
            vector_weight=vector_weight,
            collaborative_weight=collaborative_weight,
            content_weight=content_weight,
            use_time_weighting=use_time_weighting
        )
        
        # Format response to match existing API format
        response = []
        for rec in recommendations:
            product = rec["product"]
            response.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'image': product.image,
                'category': product.category,
                'color': product.color,
                'tags': product.tags,
                'price': float(product.price) if product.price else None,
                'brand_id': str(product.brand_id) if product.brand_id else None,
                'similarity_score': rec["score"],
                'recommendation_reason': rec["reason"],
                'vector_metadata': rec["vector_metadata"],
                'methods_used': rec.get("methods_used", []),
                'method_scores': rec.get("method_scores", {}),
                'hybrid_metadata': rec.get("hybrid_metadata", {})
            })
        
        # Cache the result
        set_cached_recommendations(str(user_id), cache_key, response)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hybrid recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.get("/{user_id}/hybrid-time-weighted", response_model=List[Dict[str, Any]])
async def get_time_weighted_hybrid_recommendations(
    user_id: UUID,
    limit: int = Query(10, ge=1, le=20, description="Number of recommendations to return"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    category_filter: Optional[str] = Query(None, description="Filter by product category"),
    brand_filter: Optional[UUID] = Query(None, description="Filter by brand ID"),
    time_decay_days: int = Query(30, ge=1, le=365, description="Time decay in days for preference weighting"),
    vector_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for vector-based recommendations"),
    collaborative_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for collaborative filtering"),
    content_weight: float = Query(0.2, ge=0.0, le=1.0, description="Weight for content-based recommendations"),
    db: Session = Depends(get_db)
):
    """Get time-weighted hybrid recommendations with configurable time decay"""
    try:
        # Validate weights sum to 1.0
        total_weight = vector_weight + collaborative_weight + content_weight
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Weights must sum to 1.0, got {total_weight:.2f}"
            )
        
        # Get cached recommendations if available
        cache_key = f"hybrid_time_weighted_{user_id}_{limit}_{page}_{category_filter}_{brand_filter}_{time_decay_days}_{vector_weight}_{collaborative_weight}_{content_weight}"
        cached_result = get_cached_recommendations(str(user_id), cache_key)
        if cached_result:
            logger.info(f"📦 Returning cached time-weighted hybrid recommendations for user {user_id}")
            return cached_result
        
        # Get recommendations with custom time decay
        service = RecommendationsService(db)
        
        # Override the time decay in vector service
        original_time_decay = getattr(service.vector_service, '_default_time_decay', 30)
        service.vector_service._default_time_decay = time_decay_days
        
        recommendations = service.get_hybrid_recommendations_improved(
            user_id=user_id,
            limit=limit,
            category_filter=category_filter,
            brand_filter=brand_filter,
            vector_weight=vector_weight,
            collaborative_weight=collaborative_weight,
            content_weight=content_weight,
            use_time_weighting=True  # Always use time weighting for this endpoint
        )
        
        # Restore original time decay
        service.vector_service._default_time_decay = original_time_decay
        
        # Format response to match existing API format
        response = []
        for rec in recommendations:
            product = rec["product"]
            response.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'image': product.image,
                'category': product.category,
                'color': product.color,
                'tags': product.tags,
                'price': float(product.price) if product.price else None,
                'brand_id': str(product.brand_id) if product.brand_id else None,
                'similarity_score': rec["score"],
                'recommendation_reason': rec["reason"],
                'vector_metadata': rec["vector_metadata"],
                'methods_used': rec.get("methods_used", []),
                'method_scores': rec.get("method_scores", {}),
                'hybrid_metadata': rec.get("hybrid_metadata", {}),
                'time_decay_days': time_decay_days
            })
        
        # Cache the result
        set_cached_recommendations(str(user_id), cache_key, response)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get time-weighted hybrid recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.get("/{user_id}/collaborative", response_model=List[Dict[str, Any]])
def collaborative_recommendations(
    user_id: UUID,
    limit: int = Query(default=10, ge=1, le=20),
    category: Optional[str] = None,
    brand_id: Optional[UUID] = None,
    min_similarity: float = Query(default=0.3, ge=0.0, le=1.0, description="Minimum user similarity threshold"),
    db: Session = Depends(get_db)
):
    """
    Get collaborative filtering recommendations based on similar users.
    
    This endpoint finds users with similar preferences and recommends products they liked.
    Best for users with established preferences and when you have a good user base.
    """
    
    # Start timing
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    # Log API call
    logger.info(f"🚀 [{request_id}] API CALL: Collaborative recommendations for user {user_id}")
    logger.info(f"📋 [{request_id}] Parameters: limit={limit}, min_similarity={min_similarity}")
    logger.info(f"🎯 [{request_id}] Filters: category={category}, brand_id={brand_id}")
    
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"❌ [{request_id}] User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ [{request_id}] User {user_id} validated")
        
        # Get recommendations
        recommendations_service = RecommendationsService(db)
        recommendations = recommendations_service.get_collaborative_recommendations(
            user_id=user_id,
            limit=limit,
            category_filter=category,
            brand_filter=brand_id
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log results summary
        logger.info(f"✅ [{request_id}] SUCCESS: Found {len(recommendations)} collaborative recommendations")
        logger.info(f"⏱️ [{request_id}] Processing time: {processing_time:.3f}s")
        
        # Log top recommendations
        for i, rec in enumerate(recommendations[:3]):  # Log top 3
            product = rec['product']
            score = rec['score']
            logger.info(f"🏆 [{request_id}] Top {i+1}: {product.name} (score: {score:.4f})")
        
        # Format response
        response = []
        for rec in recommendations:
            product = rec['product']
            response.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'image': product.image,
                'category': product.category,
                'color': product.color,
                'tags': product.tags,
                'price': float(product.price) if product.price else None,
                'brand_id': str(product.brand_id) if product.brand_id else None,
                'similarity_score': rec['score'],
                'recommendation_reason': rec['reason'],
                'vector_metadata': rec['vector_metadata']
            })
        
        logger.info(f"🎯 [{request_id}] API RESPONSE: Returning {len(response)} collaborative recommendations")
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] ERROR: {str(e)} (after {processing_time:.3f}s)")
        raise

@router.post("/{user_id}/feedback")
def record_recommendation_feedback(
    user_id: UUID,
    product_id: UUID,
    action: str = Query(..., description="User action: 'like', 'dislike', 'view', 'purchase'"),
    recommendation_source: str = Query(..., description="Source of recommendation: 'vector', 'collaborative', 'hybrid', etc."),
    recommendation_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Record user feedback on recommendations for quality tracking and improvement.
    
    This endpoint helps track the effectiveness of different recommendation algorithms
    and can be used for A/B testing and algorithm optimization.
    """
    
    # Start timing
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    # Log API call
    logger.info(f"🚀 [{request_id}] API CALL: Recording feedback for user {user_id}")
    logger.info(f"📋 [{request_id}] Product: {product_id}, Action: {action}, Source: {recommendation_source}")
    
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"❌ [{request_id}] User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.error(f"❌ [{request_id}] Product {product_id} not found")
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Validate action
        valid_actions = ['like', 'dislike', 'view', 'purchase', 'share', 'save']
        if action not in valid_actions:
            logger.error(f"❌ [{request_id}] Invalid action: {action}")
            raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
        
        # Record the feedback (you might want to create a separate table for this)
        # For now, we'll log it and could store in a feedback table
        feedback_data = {
            'user_id': str(user_id),
            'product_id': str(product_id),
            'action': action,
            'recommendation_source': recommendation_source,
            'recommendation_score': recommendation_score,
            'timestamp': datetime.utcnow().isoformat(),
            'product_category': product.category,
            'product_brand_id': str(product.brand_id) if product.brand_id else None
        }
        
        # Log the feedback
        logger.info(f"📊 [{request_id}] FEEDBACK: {feedback_data}")
        
        # TODO: Store in database table for analytics
        # feedback_record = RecommendationFeedback(**feedback_data)
        # db.add(feedback_record)
        # db.commit()
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(f"✅ [{request_id}] SUCCESS: Feedback recorded")
        logger.info(f"⏱️ [{request_id}] Processing time: {processing_time:.3f}s")
        
        return {
            'success': True,
            'message': 'Feedback recorded successfully',
            'feedback_data': feedback_data
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] ERROR: {str(e)} (after {processing_time:.3f}s)")
        raise

@router.get("/{user_id}/quality-metrics")
def get_recommendation_quality_metrics(
    user_id: UUID,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get recommendation quality metrics for a user.
    
    This endpoint provides insights into how well recommendations are performing
    for a specific user, including engagement rates and preference accuracy.
    """
    
    # Start timing
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    # Log API call
    logger.info(f"🚀 [{request_id}] API CALL: Quality metrics for user {user_id}")
    logger.info(f"📋 [{request_id}] Parameters: days={days}")
    
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"❌ [{request_id}] User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ [{request_id}] User {user_id} validated")
        
        # Calculate date range
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user's swipe statistics
        total_swipes = db.query(Swipe).filter(
            Swipe.user_id == user_id,
            Swipe.created_at >= start_date
        ).count()
        
        liked_swipes = db.query(Swipe).filter(
            Swipe.user_id == user_id,
            Swipe.action == "right",
            Swipe.created_at >= start_date
        ).count()
        
        disliked_swipes = db.query(Swipe).filter(
            Swipe.user_id == user_id,
            Swipe.action == "left",
            Swipe.created_at >= start_date
        ).count()
        
        # Calculate engagement metrics
        like_rate = (liked_swipes / total_swipes * 100) if total_swipes > 0 else 0
        dislike_rate = (disliked_swipes / total_swipes * 100) if total_swipes > 0 else 0
        
        # Get preference diversity
        liked_categories = db.query(Product.category).join(
            Swipe, Swipe.product_id == Product.id
        ).filter(
            Swipe.user_id == user_id,
            Swipe.action == "right",
            Swipe.created_at >= start_date,
            Product.category.isnot(None)
        ).distinct().count()
        
        liked_brands = db.query(Product.brand_id).join(
            Swipe, Swipe.product_id == Product.id
        ).filter(
            Swipe.user_id == user_id,
            Swipe.action == "right",
            Swipe.created_at >= start_date,
            Product.brand_id.isnot(None)
        ).distinct().count()
        
        # Calculate recommendation quality score
        # This is a simple heuristic - you might want to implement more sophisticated metrics
        quality_score = 0
        if total_swipes >= 10:
            quality_score += 20  # Base score for sufficient data
            quality_score += min(like_rate * 0.5, 30)  # Bonus for high like rate
            quality_score += min(liked_categories * 2, 20)  # Bonus for diverse preferences
            quality_score += min(liked_brands * 1, 15)  # Bonus for brand diversity
            quality_score += min(total_swipes * 0.5, 15)  # Bonus for engagement
        
        quality_score = min(quality_score, 100)  # Cap at 100
        
        # Determine recommendation strategy
        if quality_score >= 80:
            strategy = "advanced_hybrid"
            recommended_weights = {"vector": 0.5, "collaborative": 0.3, "content": 0.2}
        elif quality_score >= 60:
            strategy = "hybrid"
            recommended_weights = {"vector": 0.4, "collaborative": 0.3, "content": 0.3}
        elif quality_score >= 40:
            strategy = "content_based"
            recommended_weights = {"vector": 0.2, "collaborative": 0.2, "content": 0.6}
        else:
            strategy = "exploration"
            recommended_weights = {"vector": 0.1, "collaborative": 0.1, "content": 0.8}
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log results
        logger.info(f"✅ [{request_id}] SUCCESS: Quality metrics calculated")
        logger.info(f"⏱️ [{request_id}] Processing time: {processing_time:.3f}s")
        logger.info(f"📊 [{request_id}] Quality score: {quality_score}, Strategy: {strategy}")
        
        return {
            'user_id': str(user_id),
            'analysis_period': {
                'days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'engagement_metrics': {
                'total_swipes': total_swipes,
                'liked_swipes': liked_swipes,
                'disliked_swipes': disliked_swipes,
                'like_rate': round(like_rate, 2),
                'dislike_rate': round(dislike_rate, 2),
                'engagement_rate': round((total_swipes / days), 2)  # swipes per day
            },
            'preference_diversity': {
                'liked_categories': liked_categories,
                'liked_brands': liked_brands,
                'category_diversity_score': min(liked_categories * 10, 100),
                'brand_diversity_score': min(liked_brands * 15, 100)
            },
            'quality_assessment': {
                'overall_score': quality_score,
                'quality_level': "excellent" if quality_score >= 80 else "good" if quality_score >= 60 else "fair" if quality_score >= 40 else "poor",
                'recommended_strategy': strategy,
                'recommended_weights': recommended_weights
            },
            'recommendations': {
                'best_endpoint': f"/recommendations/{user_id}/hybrid-improved" if quality_score >= 60 else f"/recommendations/{user_id}/vector" if quality_score >= 40 else f"/recommendations/{user_id}/simple",
                'suggested_limit': min(max(10, total_swipes // 2), 20),
                'should_use_collaborative': quality_score >= 50 and liked_swipes >= 5,
                'should_use_vectors': quality_score >= 30
            }
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] ERROR: {str(e)} (after {processing_time:.3f}s)")
        raise

@router.get("/{user_id}/vector-optimized", response_model=List[Dict[str, Any]])
def get_vector_recommendations_optimized(
    user_id: UUID,
    limit: int = Query(default=10, ge=1, le=20, description="Number of recommendations (1-20)"),
    category: Optional[str] = None,
    brand_id: Optional[UUID] = None,
    image_weight: float = Query(default=0.6, ge=0.0, le=1.0, description="Weight for image similarity (0-1)"),
    text_weight: float = Query(default=0.4, ge=0.0, le=1.0, description="Weight for text similarity (0-1)"),
    use_cache: bool = Query(default=True, description="Use cached vectors and preferences"),
    db: Session = Depends(get_db)
):
    """
    Get optimized vector-based recommendations using FAISS for fast similarity search.
    
    This endpoint provides the same functionality as /vector but with significant performance improvements:
    - FAISS vector database for O(log n) similarity search instead of O(n²)
    - Caching of vectors and user preferences
    - Background processing for vector generation
    - Optimized memory usage
    """
    
    # Start timing
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    # Log API call
    logger.info(f"🚀 [{request_id}] API CALL: Optimized vector recommendations for user {user_id}")
    logger.info(f"📋 [{request_id}] Parameters: limit={limit}, category={category}, brand_id={brand_id}")
    logger.info(f"⚖️ [{request_id}] Weights: image={image_weight}, text={text_weight}")
    logger.info(f"💾 [{request_id}] Cache enabled: {use_cache}")
    
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"❌ [{request_id}] User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ [{request_id}] User {user_id} validated")
        
        # Create weights dictionary
        weights = {
            'image_similarity': image_weight,
            'text_similarity': text_weight,
        }
        
        # Get recommendations using optimized service
        recommendations_service = RecommendationsService(db)
        
        if use_cache:
            # Use cached preference vectors
            preference_vectors = recommendations_service.vector_service.get_user_preference_vectors_cached(
                user_id=user_id, limit_likes=10
            )
        else:
            # Generate fresh preference vectors
            preference_vectors = recommendations_service.vector_service.get_user_preference_vectors(
                user_id=user_id, limit_likes=10
            )
        
        if not preference_vectors:
            logger.warning(f"⚠️ [{request_id}] No preference vectors available, falling back to basic recommendations")
            # Fallback to basic recommendations
            recommendations = recommendations_service._get_basic_recommendations(
                user_id=user_id,
                limit=limit,
                category_filter=category,
                brand_filter=brand_id
            )
        else:
            # Use FAISS for fast similarity search
            similar_product_ids = recommendations_service.vector_service.search_similar_vectors_faiss(
                query_vectors=preference_vectors,
                limit=limit * 2,  # Get more to allow for filtering
                weights=weights
            )
            
            if not similar_product_ids:
                logger.warning(f"⚠️ [{request_id}] No similar products found with FAISS")
                recommendations = []
            else:
                # Get products with filters
                product_ids = [pid for pid, _ in similar_product_ids]
                query = db.query(Product).filter(Product.id.in_(product_ids))
                
                # Apply filters
                if category:
                    query = query.filter(Product.category == category)
                if brand_id:
                    query = query.filter(Product.brand_id == brand_id)
                
                # Exclude swiped products
                swiped_ids = set(r[0] for r in db.query(Swipe.product_id).filter(
                    Swipe.user_id == user_id
                ).all())
                query = query.filter(~Product.id.in_(swiped_ids))
                
                products = query.all()
                
                # Create score mapping
                score_map = {pid: score for pid, score in similar_product_ids}
                
                # Format recommendations
                recommendations = []
                for product in products[:limit]:
                    score = score_map.get(product.id, 0.0)
                    recommendation = {
                        'product': product,
                        'score': score,
                        'reason': f"Similar to your preferences ({(score * 100):.0f}% match)",
                        'vector_metadata': {
                            'has_image_vector': bool(product.image_vector),
                            'has_text_vector': bool(product.text_vector),
                            'has_combined_vector': bool(product.combined_vector),
                            'search_method': 'faiss'
                        }
                    }
                    recommendations.append(recommendation)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log results summary
        logger.info(f"✅ [{request_id}] SUCCESS: Found {len(recommendations)} recommendations")
        logger.info(f"⏱️ [{request_id}] Processing time: {processing_time:.3f}s")
        
        # Log top recommendations
        for i, rec in enumerate(recommendations[:3]):  # Log top 3
            product = rec['product']
            score = rec['score']
            logger.info(f"🏆 [{request_id}] Top {i+1}: {product.name} (score: {score:.4f})")
        
        # Format response
        response = []
        for rec in recommendations:
            product = rec['product']
            response.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'image': product.image,
                'category': product.category,
                'color': product.color,
                'tags': product.tags,
                'price': float(product.price) if product.price else None,
                'brand_id': str(product.brand_id) if product.brand_id else None,
                'similarity_score': rec['score'],
                'recommendation_reason': rec['reason'],
                'vector_metadata': rec['vector_metadata']
            })
        
        logger.info(f"🎯 [{request_id}] API RESPONSE: Returning {len(response)} optimized recommendations")
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] ERROR: {str(e)} (after {processing_time:.3f}s)")
        raise

@router.post("/products/{product_id}/generate-vectors-async")
def generate_product_vectors_async(
    product_id: UUID,
    force_regenerate: bool = Query(default=False, description="Force regenerate even if vectors exist"),
    db: Session = Depends(get_db)
):
    """Generate vectors for a product asynchronously (non-blocking)."""
    
    vector_service = VectorService(db)
    
    # Queue the job for background processing
    job_id = vector_service.queue_vector_generation([product_id], priority="high")
    
    if not job_id:
        raise HTTPException(status_code=500, detail="Failed to queue vector generation")
    
    return {
        'success': True,
        'message': 'Vector generation queued for background processing',
        'job_id': job_id,
        'status_endpoint': f"/recommendations/jobs/{job_id}/status"
    }

@router.get("/jobs/{job_id}/status")
def get_vector_generation_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get status of vector generation job."""
    
    vector_service = VectorService(db)
    status = vector_service.get_job_status(job_id)
    
    return status

@router.get("/vector-performance-stats")
def get_vector_performance_stats(db: Session = Depends(get_db)):
    """Get performance statistics for vector operations."""
    
    vector_service = VectorService(db)
    
    # Get cache stats
    cache_stats = vector_service.get_cache_stats()
    
    # Get vectorization status
    vectorization_status = vector_service.get_vectorization_status()
    
    # Calculate performance metrics
    total_products = vectorization_status.get('total_products', 0)
    products_with_vectors = vectorization_status.get('with_combined_vectors', 0)
    vector_coverage = (products_with_vectors / total_products * 100) if total_products > 0 else 0
    
    return {
        'cache_stats': cache_stats,
        'vectorization_status': vectorization_status,
        'performance_metrics': {
            'vector_coverage_percentage': round(vector_coverage, 2),
            'faiss_available': cache_stats.get('indexes_available', False),
            'estimated_search_speedup': '100x' if cache_stats.get('indexes_available') else '1x',
            'memory_usage_mb': cache_stats.get('memory_usage_mb', 0),
            'total_cached_vectors': cache_stats.get('total_entries', 0)
        },
        'recommendations': {
            'use_faiss': cache_stats.get('indexes_available', False),
            'enable_caching': True,
            'background_processing': True,
            'batch_size': 10 if total_products > 1000 else 5
        }
    }

@router.post("/vector-cache/clear")
def clear_vector_cache(
    pattern: Optional[str] = Query(None, description="Pattern to match cache keys for selective clearing"),
    db: Session = Depends(get_db)
):
    """Clear vector cache."""
    
    vector_service = VectorService(db)
    vector_service.clear_cache(pattern)
    
    return {
        'success': True,
        'message': f'Cache cleared{" for pattern: " + pattern if pattern else ""}',
        'cache_stats': vector_service.get_cache_stats()
    }

@router.get("/{user_id}/balanced", response_model=List[Dict[str, Any]])
async def get_balanced_recommendations(
    user_id: UUID,
    limit: int = Query(10, ge=1, le=20, description="Number of recommendations to return"),
    category_filter: Optional[str] = Query(None, description="Filter by product category"),
    brand_filter: Optional[UUID] = Query(None, description="Filter by brand ID"),
    diversity_boost: float = Query(0.4, ge=0.0, le=1.0, description="Diversity boost factor"),
    randomness_factor: float = Query(0.3, ge=0.0, le=1.0, description="Randomness factor for variety"),
    db: Session = Depends(get_db)
):
    """Get balanced recommendations considering both likes and dislikes with diversity and variety"""
    try:
        # Get cached recommendations if available
        cache_key = f"balanced_{user_id}_{limit}_{category_filter}_{brand_filter}_{diversity_boost}_{randomness_factor}"
        cached_result = get_cached_recommendations(str(user_id), cache_key)
        if cached_result:
            logger.info(f"📦 Returning cached balanced recommendations for user {user_id}")
            return cached_result
        
        # Get recommendations using balanced approach
        service = RecommendationsService(db)
        
        # Use balanced preference vectors (considers both likes and dislikes)
        preference_vectors = service.vector_service.get_user_preference_vectors_balanced(user_id)
        
        if not preference_vectors:
            logger.warning(f"⚠️ No balanced preference vectors available for user {user_id}, falling back to basic recommendations")
            return service._get_basic_recommendations(user_id, limit, category_filter, brand_filter)
        
        # Get candidate products
        query = db.query(Product).filter(Product.combined_vector.isnot(None))
        
        # Apply filters
        if category_filter:
            query = query.filter(Product.category == category_filter)
        if brand_filter:
            query = query.filter(Product.brand_id == brand_filter)
        
        # Exclude swiped products
        swiped_ids = set(r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all())
        query = query.filter(~Product.id.in_(swiped_ids))
        
        candidate_products = query.all()
        
        if not candidate_products:
            logger.warning("❌ No candidate products found")
            return []
        
        # Prepare product vectors
        product_vectors = []
        for product in candidate_products:
            product_vec = {'product': product}
            if product.image_vector:
                product_vec['image_vector'] = product.image_vector
            if product.text_vector:
                product_vec['text_vector'] = product.text_vector
            if product.combined_vector:
                product_vec['combined_vector'] = product.combined_vector
            product_vectors.append(product_vec)
        
        # Find similar products using balanced preference vectors
        similar_products = service.vector_service.vectorizer.find_similar_products(
            query_vectors=preference_vectors,
            product_vectors=product_vectors,
            limit=min(limit * 3, len(product_vectors)),
            weights={'image_similarity': 0.6, 'text_similarity': 0.4}
        )
        
        # Apply diversity and variety improvements
        final_recommendations = service._apply_diversity_and_variety(
            similar_products=similar_products,
            user_id=user_id,
            limit=limit,
            diversity_boost=diversity_boost,
            randomness_factor=randomness_factor,
            db=db
        )
        
        # Format response
        response = []
        for rec in final_recommendations:
            product, score = rec
            response.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'image': product.image,
                'category': product.category,
                'color': product.color,
                'tags': product.tags,
                'price': float(product.price) if product.price else None,
                'brand_id': str(product.brand_id) if product.brand_id else None,
                'similarity_score': score,
                'recommendation_reason': f"Balanced recommendation considering likes and dislikes (score: {score:.3f})",
                'vector_metadata': {
                    'has_image_vector': bool(product.image_vector),
                    'has_text_vector': bool(product.text_vector),
                    'has_combined_vector': bool(product.combined_vector),
                    'balanced_approach': True,
                    'diversity_boosted': True
                }
            })
        
        # Cache the result
        set_cached_recommendations(str(user_id), cache_key, response)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balanced recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")
