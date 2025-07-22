from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.db import get_db
from app.models import Swipe, Product
from app.schemas import Product as ProductSchema
from app.utils.vectorization import cosine_similarity
from sqlalchemy.sql.expression import func as sql_func

router = APIRouter()

@router.get("/{user_id}", response_model=List[ProductSchema])
def recommend(user_id: UUID, limit: int = 10, db: Session = Depends(get_db)):
    """Get product recommendations for a user based on their swipe history."""
    
    # Check total products available
    total_products = db.query(Product).count()
    
    # Check how many products user has swiped
    user_swipes_count = db.query(Swipe).filter(Swipe.user_id == user_id).count()
    
    # If user has swiped on all products, return empty with message
    if user_swipes_count >= total_products and total_products > 0:
        # This will return an empty list but with HTTP 200
        return []
    
    # Get user's right swipes (liked products)
    liked_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id, 
        Swipe.direction == "right"
    ).all()
    
    # Get user's left swipes (disliked products)
    disliked_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id, 
        Swipe.direction == "left"
    ).all()
    
    if not liked_swipes:
        # If no likes, return popular products (most right-swiped)
        # Get products user hasn't swiped on yet
        swiped_product_ids = set(
            r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all()
        )
        
        popular_products = db.query(Product).filter(
            ~Product.id.in_(swiped_product_ids)
        ).order_by(Product.swipe_right_count.desc()).limit(limit).all()
        return popular_products
    
    # Get liked product IDs
    liked_product_ids = [swipe.product_id for swipe in liked_swipes]
    
    # Get disliked product IDs
    disliked_product_ids = [swipe.product_id for swipe in disliked_swipes]
    
    # Get liked products details
    liked_products = db.query(Product).filter(
        Product.id.in_(liked_product_ids)
    ).all()
    
    # Get disliked products details
    disliked_products = db.query(Product).filter(
        Product.id.in_(disliked_product_ids)
    ).all()
    
    # Extract positive preferences from liked products
    liked_categories = [p.category for p in liked_products if p.category]
    liked_tags = []
    liked_brands = [p.brand_id for p in liked_products if p.brand_id]
    
    for product in liked_products:
        if product.tags:
            liked_tags.extend(product.tags)
    
    # Extract negative preferences from disliked products
    disliked_categories = [p.category for p in disliked_products if p.category]
    disliked_tags = []
    disliked_brands = [p.brand_id for p in disliked_products if p.brand_id]
    
    for product in disliked_products:
        if product.tags:
            disliked_tags.extend(product.tags)
    
    # Get products user has swiped on yet (as a set for Python logic)
    swiped_product_ids = set(
        r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all()
    )
    
    # Build recommendation query - exclude swiped products
    query = db.query(Product).filter(
        ~Product.id.in_(swiped_product_ids)
    )
    
    # Score products based on preferences
    recommendations = []
    
    # Method 1: Same categories as liked (but avoid disliked categories)
    if liked_categories:
        # Filter out disliked categories
        preferred_categories = [cat for cat in liked_categories if cat not in disliked_categories]
        
        if preferred_categories:
            category_matches = query.filter(
                Product.category.in_(preferred_categories)
            ).limit(limit // 2).all()
            recommendations.extend(category_matches)
    
    # Method 2: Same brands as liked (but avoid disliked brands)
    if liked_brands:
        # Filter out disliked brands
        preferred_brands = [brand for brand in liked_brands if brand not in disliked_brands]
        
        if preferred_brands:
            brand_matches = query.filter(
                Product.brand_id.in_(preferred_brands),
                ~Product.id.in_([r.id for r in recommendations])
            ).limit(limit // 3).all()
            recommendations.extend(brand_matches)
    
    # Method 3: Similar tags as liked (but avoid disliked tags)
    if liked_tags:
        # Filter out disliked tags
        preferred_tags = [tag for tag in set(liked_tags) if tag not in set(disliked_tags)]
        
        for tag in preferred_tags[:3]:  # Top 3 most common preferred tags
            tag_matches = query.filter(
                Product.tags.any(tag),
                ~Product.id.in_([r.id for r in recommendations])
            ).limit(2).all()
            recommendations.extend(tag_matches)
    
    # Vector-based recommendations
    if liked_products:
        liked_vectors = [p.vector_id_combined for p in liked_products if p.vector_id_combined]
        
        # Check if user has any likes
        if not liked_swipes:
            # Return 5 random products if no likes
            random_products = db.query(Product).filter(
                ~Product.id.in_(swiped_product_ids)
            ).order_by(sql_func.random()).limit(5).all()
            recommendations.extend(random_products)
        else:
            # Use last likes for vector-based recommendations
            last_likes = db.query(Swipe).filter(
                Swipe.user_id == user_id,
                Swipe.direction == "right"
            ).order_by(Swipe.timestamp.desc()).limit(5).all()
            
            last_vectors = [swipe.product.vector_id_combined for swipe in last_likes if swipe.product and swipe.product.vector_id_combined]
            
            # Get all products with vectors that haven't been swiped
            all_products_with_vectors = db.query(Product).filter(
                Product.vector_id_combined != None,
                ~Product.id.in_(swiped_product_ids)
            ).all()
            
            # Calculate similarity and sort
            vector_recommendations = []
            if last_vectors:  # Only proceed if there are actual vectors from liked products
                for product in all_products_with_vectors:
                    # Ensure product has a vector before calculating similarity
                    if product.vector_id_combined:
                        similarities = [cosine_similarity(last_vector, product.vector_id_combined) for last_vector in last_vectors]
                        max_similarity = max(similarities) if similarities else 0
                        vector_recommendations.append((product, max_similarity))
                
                # Sort by similarity
                vector_recommendations.sort(key=lambda x: x[1], reverse=True)
                
                # Add top vector-based recommendations
                recommendations.extend([v[0] for v in vector_recommendations[:limit]])

    # Ensure unique recommendations
    recommendations = list({r.id: r for r in recommendations}.values())

    # Fill remaining slots with popular products if not enough recommendations
    remaining_slots = limit - len(recommendations)
    if remaining_slots > 0:
        popular_fills = db.query(Product).filter(
            ~Product.id.in_(swiped_product_ids),
            ~Product.id.in_([r.id for r in recommendations])
        ).order_by(Product.swipe_right_count.desc()).limit(remaining_slots).all()
        recommendations.extend(popular_fills)

    return recommendations[:limit]

@router.get("/{user_id}/simple")
def simple_recommendations(user_id: UUID, limit: int = 5, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get simple product recommendations based on user's liked categories."""
    
    # Check total products and user swipes
    total_products = db.query(Product).count()
    user_swipes_count = db.query(Swipe).filter(Swipe.user_id == user_id).count()
    
    # If user has swiped on all products
    if user_swipes_count >= total_products and total_products > 0:
        # Get user's stats
        total_likes = db.query(Swipe).filter(
            Swipe.user_id == user_id, 
            Swipe.direction == "right"
        ).count()
        
        return {
            "message": "🎉 You've swiped on all available products!",
            "status": "all_products_swiped",
            "recommendations": [],
            "stats": {
                "total_products_swiped": user_swipes_count,
                "total_products_available": total_products,
                "total_likes": total_likes,
                "like_percentage": round((total_likes / user_swipes_count) * 100, 1) if user_swipes_count > 0 else 0
            },
            "suggestions": [
                "Check your wishlist for saved items",
                "Browse brands you liked the most",
                "New products may be added soon - check back later!",
                "Explore different categories you haven't tried yet"
            ]
        }
    
    # Get user's right swipes
    liked_swipes = db.query(Swipe, Product).join(Product, Swipe.product_id == Product.id).filter(
        Swipe.user_id == user_id,
        Swipe.direction == "right"
    ).with_entities(Product.category, Product.brand_id).all()
    
    if not liked_swipes:
        # Get unswiped products count
        swiped_product_ids = db.query(Swipe.product_id).filter(
            Swipe.user_id == user_id
        ).subquery()
        
        unswiped_count = db.query(Product).filter(
            ~Product.id.in_(swiped_product_ids)
        ).count()
        
        return {
            "message": "No likes yet - start swiping to get personalized recommendations!",
            "recommendations": [],
            "stats": {
                "products_remaining": unswiped_count,
                "total_products": total_products
            }
        }
    
    # Count category preferences
    category_counts = {}
    brand_counts = {}
    
    for swipe in liked_swipes:
        if swipe.category:
            category_counts[swipe.category] = category_counts.get(swipe.category, 0) + 1
        if swipe.brand_id:
            brand_counts[swipe.brand_id] = brand_counts.get(swipe.brand_id, 0) + 1
    
    # Get top preferences
    top_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
    top_brand = max(brand_counts.items(), key=lambda x: x[1])[0] if brand_counts else None
    
    # Get products user hasn't swiped
    swiped_products = db.query(Swipe.product_id).filter(Swipe.user_id == user_id).subquery()
    
    recommendations = []
    products_remaining = 0
    
    if top_category:
        # Try to get recommendations from top category first
        category_recs = db.query(Product).filter(
            Product.category == top_category,
            ~Product.id.in_(swiped_products)
        ).limit(limit).all()
        
        if category_recs:
            recommendations = [
                {
                    "id": str(p.id), 
                    "name": p.name, 
                    "category": p.category, 
                    "color": p.color,
                    "brand_id": str(p.brand_id) if p.brand_id else None,
                    "reason": f"You like {top_category}"
                } for p in category_recs
            ]
        else:
            # If no products in preferred category, try other categories or brands
            if top_brand:
                brand_recs = db.query(Product).filter(
                    Product.brand_id == top_brand,
                    ~Product.id.in_(swiped_products)
                ).limit(limit).all()
                
                if brand_recs:
                    recommendations = [
                        {
                            "id": str(p.id), 
                            "name": p.name, 
                            "category": p.category, 
                            "color": p.color,
                            "brand_id": str(p.brand_id) if p.brand_id else None,
                            "reason": "From your favorite brand"
                        } for p in brand_recs
                    ]
            
            # If still no recommendations, get any remaining products
            if not recommendations:
                any_remaining = db.query(Product).filter(
                    ~Product.id.in_(swiped_products)
                ).order_by(Product.swipe_right_count.desc()).limit(limit).all()
                
                if any_remaining:
                    recommendations = [
                        {
                            "id": str(p.id), 
                            "name": p.name, 
                            "category": p.category, 
                            "color": p.color,
                            "brand_id": str(p.brand_id) if p.brand_id else None,
                            "reason": "Popular product"
                        } for p in any_remaining
                    ]
    
    # Count remaining products
    products_remaining = db.query(Product).filter(
        ~Product.id.in_(swiped_products)
    ).count()
    
    return {
        "recommendations": recommendations, 
        "preferences": {
            "top_category": top_category, 
            "top_brand": str(top_brand) if top_brand else None
        },
        "stats": {
            "products_remaining": products_remaining,
            "total_products": total_products,
            "products_swiped": user_swipes_count
        }
    }

@router.get("/{user_id}/status")
def get_swipe_status(user_id: UUID, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get user's swiping progress and statistics."""
    
    total_products = db.query(Product).count()
    user_swipes = db.query(Swipe).filter(Swipe.user_id == user_id).all()
    
    total_likes = len([s for s in user_swipes if s.direction == "right"])
    total_dislikes = len([s for s in user_swipes if s.direction == "left"])
    total_swiped = len(user_swipes)
    
    remaining_products = total_products - total_swiped
    completion_percentage = round((total_swiped / total_products) * 100, 1) if total_products > 0 else 0
    
    # Check if completed
    all_swiped = total_swiped >= total_products
    
    return {
        "user_id": str(user_id),
        "all_products_swiped": all_swiped,
        "progress": {
            "total_products": total_products,
            "products_swiped": total_swiped,
            "products_remaining": remaining_products,
            "completion_percentage": completion_percentage
        },
        "swipe_stats": {
            "total_likes": total_likes,
            "total_dislikes": total_dislikes,
            "like_percentage": round((total_likes / total_swiped) * 100, 1) if total_swiped > 0 else 0
        },
        "status": "completed" if all_swiped else "in_progress"
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
    """Get hybrid recommendations combining user preferences with search query."""
    
    # Get user's preferences
    liked_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id, 
        Swipe.direction == "right"
    ).all()
    
    disliked_swipes = db.query(Swipe).filter(
        Swipe.user_id == user_id, 
        Swipe.direction == "left"
    ).all()
    
    # Get swiped product IDs
    swiped_product_ids = set(
        r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all()
    )
    
    # Base query - exclude swiped products
    query = db.query(Product).filter(~Product.id.in_(swiped_product_ids))
    
    # Apply filters
    if category:
        query = query.filter(Product.category == category)
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    
    recommendations = []
    
    if search_query and liked_swipes:
        # Hybrid approach: combine search with user preferences
        # Get user's liked product vectors
        liked_vectors = []
        for swipe in liked_swipes[:5]:  # Use last 5 likes
            if swipe.product and swipe.product.vector_id_combined:
                liked_vectors.append(swipe.product.vector_id_combined)
        
        if liked_vectors:
            # Get products matching search criteria
            search_products = query.all()
            
            # Calculate hybrid scores
            scored_products = []
            for product in search_products:
                if product.vector_id_combined:
                    # Vector similarity with liked products
                    vector_scores = [cosine_similarity(liked_vec, product.vector_id_combined) for liked_vec in liked_vectors]
                    avg_vector_score = sum(vector_scores) / len(vector_scores) if vector_scores else 0
                    
                    # Text similarity with search query
                    text_similarity = 0
                    if search_query.lower() in product.name.lower():
                        text_similarity += 0.3
                    if search_query.lower() in product.description.lower():
                        text_similarity += 0.2
                    if any(tag.lower() in search_query.lower() for tag in (product.tags or [])):
                        text_similarity += 0.1
                    
                    # Combine scores (70% vector, 30% text)
                    hybrid_score = (avg_vector_score * 0.7) + (text_similarity * 0.3)
                    scored_products.append((product, hybrid_score))
            
            # Sort by hybrid score
            scored_products.sort(key=lambda x: x[1], reverse=True)
            recommendations = [p[0] for p in scored_products[:limit]]
    
    elif search_query:
        # Pure search-based recommendations
        search_products = query.all()
        scored_products = []
        
        for product in search_products:
            score = 0
            # Name match
            if search_query.lower() in product.name.lower():
                score += 0.4
            # Description match
            if search_query.lower() in product.description.lower():
                score += 0.3
            # Tag match
            if any(tag.lower() in search_query.lower() for tag in (product.tags or [])):
                score += 0.2
            # Category match
            if search_query.lower() in (product.category or "").lower():
                score += 0.1
            
            if score > 0:
                scored_products.append((product, score))
        
        scored_products.sort(key=lambda x: x[1], reverse=True)
        recommendations = [p[0] for p in scored_products[:limit]]
    
    else:
        # Fall back to regular recommendations
        return recommend(user_id, limit, db)
    
    return recommendations[:limit]

@router.get("/{user_id}/semantic", response_model=List[ProductSchema])
def semantic_recommendations(
    user_id: UUID,
    query_text: str = Query(..., description="Natural language query"),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get semantic recommendations based on natural language query."""
    
    # Get user's swiped products
    swiped_product_ids = set(
        r[0] for r in db.query(Swipe.product_id).filter(Swipe.user_id == user_id).all()
    )
    
    # Get all products with vectors
    products_with_vectors = db.query(Product).filter(
        Product.vector_id_combined != None,
        ~Product.id.in_(swiped_product_ids)
    ).all()
    
    if not products_with_vectors:
        return []
    
    # Generate vector for the query text (simplified - you might want to use a proper text encoder)
    # For now, we'll use a simple text-based approach
    query_terms = query_text.lower().split()
    
    scored_products = []
    for product in products_with_vectors:
        score = 0
        
        # Check name relevance
        product_name_terms = product.name.lower().split()
        name_matches = sum(1 for term in query_terms if any(term in name_term for name_term in product_name_terms))
        score += name_matches * 0.3
        
        # Check description relevance
        if product.description:
            desc_terms = product.description.lower().split()
            desc_matches = sum(1 for term in query_terms if any(term in desc_term for desc_term in desc_terms))
            score += desc_matches * 0.2
        
        # Check category relevance
        if product.category and any(term in product.category.lower() for term in query_terms):
            score += 0.2
        
        # Check tag relevance
        if product.tags:
            tag_matches = sum(1 for term in query_terms if any(term in tag.lower() for tag in product.tags))
            score += tag_matches * 0.1
        
        # Check color relevance
        if product.color and any(term in product.color.lower() for term in query_terms):
            score += 0.1
        
        if score > 0:
            scored_products.append((product, score))
    
    # Sort by relevance score
    scored_products.sort(key=lambda x: x[1], reverse=True)
    
    return [p[0] for p in scored_products[:limit]]
