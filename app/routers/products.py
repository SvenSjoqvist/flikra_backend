from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, text
from typing import List, Optional
from uuid import UUID
from app.db import get_db
from app.models import Product
from app.schemas import Product as ProductSchema, ProductCreate, ProductUpdate
from app.services.vector_service import VectorService

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
    
    # Price range filter
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
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
            Product.price.asc() if sort_order == "asc" 
            else Product.price.desc()
        )
    elif sort_by == "popularity":
        # Note: swipe_right_count field doesn't exist in current model
        query = query.order_by(Product.created_at.desc())
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
        product_dict.pop('rank', None)
        products.append(Product(**product_dict))
    
    return products

async def generate_vectors_background(product_id: UUID, db: Session):
    """Background task to generate vectors for a product."""
    try:
        vector_service = VectorService(db)
        result = vector_service.generate_vectors_for_product(product_id)
        if not result['success']:
            print(f"Failed to generate vectors for product {product_id}: {result['error']}")
    except Exception as e:
        print(f"Error in background vector generation for product {product_id}: {e}")

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new product with automatic vector generation."""
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Generate vectors in background
    background_tasks.add_task(generate_vectors_background, db_product.id, db)
    
    return db_product

@router.get("/vectorization-status")
def get_vectorization_status(db: Session = Depends(get_db)):
    """Get vectorization status across all products."""
    vector_service = VectorService(db)
    status = vector_service.get_vectorization_status()
    return status

@router.post("/generate-vectors-batch")
async def generate_vectors_batch(
    product_ids: List[UUID],
    force_regenerate: bool = False,
    db: Session = Depends(get_db)
):
    """Generate vectors for multiple products in batches."""
    vector_service = VectorService(db)
    result = vector_service.generate_vectors_batch(product_ids, force_regenerate=force_regenerate)
    return result

@router.post("/generate-vectors-missing")
async def generate_vectors_for_missing_products(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Generate vectors for products that don't have them."""
    vector_service = VectorService(db)
    result = vector_service.generate_vectors_for_missing()
    return result

@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    """Get a specific product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: UUID, 
    product_update: ProductUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update a product and regenerate vectors if needed."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Regenerate vectors in background if image or text changed
    if 'image' in update_data or 'name' in update_data or 'description' in update_data:
        background_tasks.add_task(generate_vectors_background, product_id, db)
    
    return product

@router.delete("/{product_id}")
def delete_product(product_id: UUID, db: Session = Depends(get_db)):
    """Delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
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
    products_with_tags = db.query(Product.tags).filter(Product.tags.isnot(None)).all()
    all_tags = set()
    for product_tags in products_with_tags:
        if product_tags[0]:
            all_tags.update(product_tags[0])
    return list(all_tags)

@router.post("/{product_id}/generate-vectors")
async def generate_vectors_for_product(
    product_id: UUID,
    force_regenerate: bool = False,
    db: Session = Depends(get_db)
):
    """Generate vectors for a specific product."""
    vector_service = VectorService(db)
    result = vector_service.generate_vectors_for_product(product_id, force_regenerate)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

 