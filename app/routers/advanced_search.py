from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.db import get_db
from app.models import Product
from app.schemas import Product as ProductSchema
from app.services.search_service import SearchService

router = APIRouter()

@router.get("/full-text", response_model=List[ProductSchema])
def full_text_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, description="Number of results"),
    db: Session = Depends(get_db)
):
    """PostgreSQL full-text search with ranking."""
    search_service = SearchService(db)
    return search_service.full_text_search(q, limit)

@router.get("/vector", response_model=List[Dict[str, Any]])
def vector_search(
    query_text: str = Query(..., description="Text to convert to vector"),
    limit: int = Query(20, description="Number of results"),
    db: Session = Depends(get_db)
):
    """Vector similarity search (requires text-to-vector conversion)."""
    # Note: This would need integration with your CLIP text encoder
    # For now, returning a placeholder response
    return [{"message": "Vector search requires text-to-vector conversion integration"}]

@router.get("/hybrid", response_model=List[Dict[str, Any]])
def hybrid_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, description="Number of results"),
    vector_weight: float = Query(0.7, description="Weight for vector similarity (0-1)"),
    db: Session = Depends(get_db)
):
    """Hybrid search combining text and vector similarity."""
    search_service = SearchService(db)
    results = search_service.hybrid_search(q, limit=limit, vector_weight=vector_weight)
    
    return [
        {
            "product": ProductSchema.from_orm(product),
            "score": score
        }
        for product, score in results
    ]

@router.get("/filtered", response_model=List[ProductSchema])
def filtered_search(
    search_query: Optional[str] = Query(None, description="Text search query"),
    category: Optional[str] = Query(None, description="Product category"),
    gender: Optional[str] = Query(None, description="Target gender"),
    color: Optional[str] = Query(None, description="Product color"),
    brand_id: Optional[UUID] = Query(None, description="Brand ID"),
    tags: Optional[List[str]] = Query(None, description="Product tags"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    exclude_swiped_by: Optional[UUID] = Query(None, description="User ID to exclude swiped products"),
    limit: int = Query(20, description="Number of results"),
    db: Session = Depends(get_db)
):
    """Advanced filtered search with multiple criteria."""
    search_service = SearchService(db)
    return search_service.filtered_search(
        search_query=search_query,
        category=category,
        gender=gender,
        color=color,
        brand_id=brand_id,
        tags=tags,
        min_price=min_price,
        max_price=max_price,
        exclude_swiped_by=exclude_swiped_by,
        limit=limit
    )

@router.get("/semantic", response_model=List[Dict[str, Any]])
def semantic_search(
    query_text: str = Query(..., description="Natural language query"),
    limit: int = Query(20, description="Number of results"),
    db: Session = Depends(get_db)
):
    """Semantic search using natural language processing concepts."""
    search_service = SearchService(db)
    results = search_service.semantic_search(query_text, limit)
    
    return [
        {
            "product": ProductSchema.from_orm(product),
            "relevance_score": score
        }
        for product, score in results
    ]

@router.get("/suggestions", response_model=List[str])
def get_search_suggestions(
    q: str = Query(..., description="Partial search query"),
    limit: int = Query(10, description="Number of suggestions"),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on partial query."""
    search_service = SearchService(db)
    return search_service.get_search_suggestions(q, limit)

@router.get("/similar/{product_id}", response_model=List[Dict[str, Any]])
def find_similar_products(
    product_id: UUID,
    limit: int = Query(10, description="Number of similar products"),
    db: Session = Depends(get_db)
):
    """Find products similar to a given product using vector similarity."""
    # Get the target product
    target_product = db.query(Product).filter(Product.id == product_id).first()
    if not target_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not target_product.vector_id_combined:
        raise HTTPException(status_code=400, detail="Product has no vector data")
    
    # Find similar products
    search_service = SearchService(db)
    similar_products = search_service.vector_search(target_product.vector_id_combined, limit + 1)
    
    # Remove the target product from results
    similar_products = [(p, s) for p, s in similar_products if p.id != product_id]
    
    return [
        {
            "product": ProductSchema.from_orm(product),
            "similarity_score": score
        }
        for product, score in similar_products[:limit]
    ]

@router.get("/trending", response_model=List[ProductSchema])
def get_trending_products(
    limit: int = Query(10, description="Number of trending products"),
    timeframe_days: int = Query(7, description="Timeframe in days"),
    db: Session = Depends(get_db)
):
    """Get trending products based on recent swipe activity."""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Calculate date threshold
    threshold_date = datetime.utcnow() - timedelta(days=timeframe_days)
    
    # Get products with most recent right swipes
    trending_products = db.query(Product).join(
        db.query(Swipe.product_id, func.count(Swipe.id).label('recent_swipes'))
        .filter(
            Swipe.direction == "right",
            Swipe.timestamp >= threshold_date
        )
        .group_by(Swipe.product_id)
        .subquery()
    ).order_by(
        db.query(Swipe.product_id, func.count(Swipe.id).label('recent_swipes'))
        .filter(
            Swipe.direction == "right",
            Swipe.timestamp >= threshold_date
        )
        .group_by(Swipe.product_id)
        .subquery().c.recent_swipes.desc()
    ).limit(limit).all()
    
    return trending_products

@router.get("/discovery", response_model=List[ProductSchema])
def get_discovery_products(
    user_id: UUID,
    limit: int = Query(10, description="Number of discovery products"),
    db: Session = Depends(get_db)
):
    """Get discovery products - items outside user's usual preferences."""
    from app.models import Swipe
    
    # Get user's preferred categories and brands
    user_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id,
        Swipe.direction == "right"
    ).join(Product).all()
    
    if not user_swipes:
        # If no swipes, return random products
        return db.query(Product).order_by(func.random()).limit(limit).all()
    
    # Extract preferences
    preferred_categories = set()
    preferred_brands = set()
    
    for swipe in user_swipes:
        if swipe.product.category:
            preferred_categories.add(swipe.product.category)
        if swipe.product.brand_id:
            preferred_brands.add(swipe.product.brand_id)
    
    # Get swiped product IDs
    swiped_ids = set(r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all())
    
    # Find products outside preferences
    discovery_query = db.query(Product).filter(~Product.id.in_(swiped_ids))
    
    if preferred_categories:
        discovery_query = discovery_query.filter(~Product.category.in_(preferred_categories))
    if preferred_brands:
        discovery_query = discovery_query.filter(~Product.brand_id.in_(preferred_brands))
    
    return discovery_query.order_by(func.random()).limit(limit).all() 