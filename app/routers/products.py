from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, text
from typing import List, Optional
from uuid import UUID
from app.db import get_db
from app.models import Product
from app.schemas import Product as ProductSchema, ProductCreate, ProductUpdate

router = APIRouter()

@router.get("/", response_model=List[ProductSchema])
def list_products(
    skip: int = 0, 
    limit: int = 100,
    category: Optional[str] = None,
    gender: Optional[str] = None,
    color: Optional[str] = None,
    brand_id: Optional[UUID] = None,
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = Query("created_at", description="Sort by: name, price, created_at, popularity"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db)
):
    """List products with advanced filtering and search."""
    query = db.query(Product)
    
    # Basic filters
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
    
    # Price range filter (if you add price field)
    if min_price is not None:
        query = query.filter(Product.product_metadata['price'].astext.cast(float) >= min_price)
    if max_price is not None:
        query = query.filter(Product.product_metadata['price'].astext.cast(float) <= max_price)
    
    # Full-text search
    if search:
        # Create search vector from name, description, and tags
        search_query = text("""
            to_tsvector('english', 
                COALESCE(name, '') || ' ' || 
                COALESCE(description, '') || ' ' || 
                COALESCE(array_to_string(tags, ' '), '')
            ) @@ plainto_tsquery('english', :search_term)
        """)
        query = query.filter(search_query.bindparams(search_term=search))
    
    # Sorting
    if sort_by == "name":
        query = query.order_by(Product.name.asc() if sort_order == "asc" else Product.name.desc())
    elif sort_by == "price":
        query = query.order_by(
            Product.product_metadata['price'].astext.cast(float).asc() if sort_order == "asc" 
            else Product.product_metadata['price'].astext.cast(float).desc()
        )
    elif sort_by == "popularity":
        query = query.order_by(
            Product.swipe_right_count.asc() if sort_order == "asc" 
            else Product.swipe_right_count.desc()
        )
    else:  # default: created_at
        query = query.order_by(
            Product.created_at.asc() if sort_order == "asc" 
            else Product.created_at.desc()
        )
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/search/", response_model=List[ProductSchema])
def search_products(
    q: str = Query(..., description="Search query"),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Advanced product search with ranking."""
    # Use PostgreSQL full-text search with ranking
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
    
    result = db.execute(search_query, {"search_term": q, "limit": limit})
    products = []
    for row in result:
        product_dict = dict(row)
        product_dict.pop('rank', None)  # Remove rank from response
        products.append(Product(**product_dict))
    
    return products

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    """Get a specific product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductSchema)
def update_product(product_id: UUID, product_update: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(product_id: UUID, db: Session = Depends(get_db)):
    """Delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.get("/categories/", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """Get all unique product categories."""
    categories = db.query(Product.category).distinct().filter(Product.category.isnot(None)).all()
    return [cat[0] for cat in categories]

@router.get("/tags/", response_model=List[str])
def get_tags(db: Session = Depends(get_db)):
    """Get all unique product tags."""
    # This is a simplified version - you might want to use a more efficient query
    products = db.query(Product.tags).filter(Product.tags.isnot(None)).all()
    all_tags = set()
    for product_tags in products:
        if product_tags[0]:
            all_tags.update(product_tags[0])
    return list(all_tags) 