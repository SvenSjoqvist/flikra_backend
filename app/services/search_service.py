from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
from uuid import UUID
from app.models import Product, Swipe
from app.utils.vectorization import cosine_similarity
import numpy as np

class SearchService:
    """Advanced search service with multiple search strategies."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def full_text_search(self, query: str, limit: int = 20) -> List[Product]:
        """PostgreSQL full-text search with ranking."""
        search_query = text("""
            SELECT *, 
                   ts_rank(
                       to_tsvector('english', 
                           COALESCE(name, '') || ' ' || 
                           COALESCE(description, '') || ' ' || 
                           COALESCE(array_to_string(tags, ' '), '')
                       ), 
                       plainto_tsquery('english', :search_term)
                   ) as rank
            FROM products 
            WHERE to_tsvector('english', 
                COALESCE(name, '') || ' ' || 
                COALESCE(description, '') || ' ' || 
                COALESCE(array_to_string(tags, ' '), '')
            ) @@ plainto_tsquery('english', :search_term)
            ORDER BY rank DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(search_query, {"search_term": query, "limit": limit})
        products = []
        for row in result:
            product_dict = dict(row)
            product_dict.pop('rank', None)
            products.append(Product(**product_dict))
        
        return products
    
    def vector_search(self, query_vector: List[float], limit: int = 20) -> List[Tuple[Product, float]]:
        """Vector similarity search using CLIP embeddings."""
        products_with_vectors = self.db.query(Product).filter(
            Product.vector_id_combined != None
        ).all()
        
        scored_products = []
        for product in products_with_vectors:
            if product.vector_id_combined:
                similarity = cosine_similarity(query_vector, product.vector_id_combined)
                scored_products.append((product, similarity))
        
        # Sort by similarity
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return scored_products[:limit]
    
    def hybrid_search(self, text_query: str, query_vector: Optional[List[float]] = None, 
                     limit: int = 20, vector_weight: float = 0.7) -> List[Tuple[Product, float]]:
        """Combine text search with vector search."""
        # Text search results
        text_results = self.full_text_search(text_query, limit * 2)
        
        # Vector search results (if vector provided)
        vector_results = []
        if query_vector:
            vector_results = self.vector_search(query_vector, limit * 2)
        
        # Combine and score
        product_scores = {}
        
        # Add text search scores
        for i, product in enumerate(text_results):
            text_score = 1.0 - (i / len(text_results))  # Normalize by position
            product_scores[product.id] = product_scores.get(product.id, 0) + (text_score * (1 - vector_weight))
        
        # Add vector search scores
        for product, vector_score in vector_results:
            product_scores[product.id] = product_scores.get(product.id, 0) + (vector_score * vector_weight)
        
        # Sort by combined score
        scored_products = [(self.db.query(Product).filter(Product.id == pid).first(), score) 
                          for pid, score in product_scores.items()]
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        return scored_products[:limit]
    
    def filtered_search(self, 
                       search_query: Optional[str] = None,
                       category: Optional[str] = None,
                       gender: Optional[str] = None,
                       color: Optional[str] = None,
                       brand_id: Optional[UUID] = None,
                       tags: Optional[List[str]] = None,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None,
                       exclude_swiped_by: Optional[UUID] = None,
                       limit: int = 20) -> List[Product]:
        """Advanced filtered search with multiple criteria."""
        query = self.db.query(Product)
        
        # Apply filters
        if category:
            query = query.filter(Product.category == category)
        if gender:
            query = query.filter(Product.gender == gender)
        if color:
            query = query.filter(Product.color.ilike(f"%{color}%"))
        if brand_id:
            query = query.filter(Product.brand_id == brand_id)
        if tags:
            for tag in tags:
                query = query.filter(Product.tags.any(tag))
        if min_price is not None:
            query = query.filter(Product.product_metadata['price'].astext.cast(float) >= min_price)
        if max_price is not None:
            query = query.filter(Product.product_metadata['price'].astext.cast(float) <= max_price)
        if exclude_swiped_by:
            swiped_ids = set(r[0] for r in self.db.query(Swipe.product_id).filter(Swipe.user_id == exclude_swiped_by).all())
            query = query.filter(~Product.id.in_(swiped_ids))
        
        # Apply text search if provided
        if search_query:
            search_query_sql = text("""
                to_tsvector('english', 
                    COALESCE(name, '') || ' ' || 
                    COALESCE(description, '') || ' ' || 
                    COALESCE(array_to_string(tags, ' '), '')
                ) @@ plainto_tsquery('english', :search_term)
            """)
            query = query.filter(search_query_sql.bindparams(search_term=search_query))
        
        return query.limit(limit).all()
    
    def semantic_search(self, query_text: str, limit: int = 20) -> List[Tuple[Product, float]]:
        """Semantic search using natural language processing concepts."""
        query_terms = query_text.lower().split()
        
        # Get all products
        products = self.db.query(Product).all()
        
        scored_products = []
        for product in products:
            score = 0
            
            # Name relevance
            product_name_terms = product.name.lower().split()
            name_matches = sum(1 for term in query_terms if any(term in name_term for name_term in product_name_terms))
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
        
        # Sort by relevance score
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return scored_products[:limit]
    
    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query."""
        suggestions = set()
        
        # Get suggestions from product names
        name_suggestions = self.db.query(Product.name).filter(
            Product.name.ilike(f"%{partial_query}%")
        ).limit(limit).all()
        suggestions.update([name[0] for name in name_suggestions])
        
        # Get suggestions from categories
        category_suggestions = self.db.query(Product.category).filter(
            Product.category.ilike(f"%{partial_query}%")
        ).distinct().limit(limit).all()
        suggestions.update([cat[0] for cat in category_suggestions if cat[0]])
        
        # Get suggestions from tags
        products_with_tags = self.db.query(Product.tags).filter(
            Product.tags.isnot(None)
        ).all()
        for product_tags in products_with_tags:
            if product_tags[0]:
                matching_tags = [tag for tag in product_tags[0] if partial_query.lower() in tag.lower()]
                suggestions.update(matching_tags)
        
        return list(suggestions)[:limit] 