from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db import get_db
from app.models import BrandAnalyticsEvent, Brand, Product, User
from app.schemas import BrandAnalyticsEvent as AnalyticsEventSchema, BrandAnalyticsEventCreate

router = APIRouter()

@router.post("/", response_model=AnalyticsEventSchema, status_code=status.HTTP_201_CREATED)
def track_event(event: BrandAnalyticsEventCreate, request: Request, db: Session = Depends(get_db)):
    """Track a brand analytics event."""
    # Validate brand exists
    brand = db.query(Brand).filter(Brand.id == event.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Validate product exists if product_id is provided
    if event.product_id:
        product = db.query(Product).filter(Product.id == event.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate user exists if user_id is provided
    if event.user_id:
        user = db.query(User).filter(User.id == event.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    # Extract IP address from request
    client_ip = request.client.host if request.client else None
    
    # Create analytics event
    event_data = event.dict()
    if not event_data.get("ip_address") and client_ip:
        event_data["ip_address"] = client_ip
    
    db_event = BrandAnalyticsEvent(**event_data)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event

@router.get("/brand/{brand_id}", response_model=List[AnalyticsEventSchema])
def get_brand_events(
    brand_id: UUID,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get analytics events for a specific brand."""
    query = db.query(BrandAnalyticsEvent).filter(BrandAnalyticsEvent.brand_id == brand_id)
    
    if event_type:
        query = query.filter(BrandAnalyticsEvent.event_type == event_type)
    
    events = query.order_by(BrandAnalyticsEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return events

@router.get("/product/{product_id}", response_model=List[AnalyticsEventSchema])
def get_product_events(
    product_id: UUID,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get analytics events for a specific product."""
    query = db.query(BrandAnalyticsEvent).filter(BrandAnalyticsEvent.product_id == product_id)
    
    if event_type:
        query = query.filter(BrandAnalyticsEvent.event_type == event_type)
    
    events = query.order_by(BrandAnalyticsEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return events

@router.get("/stats/brand/{brand_id}")
def get_brand_stats(brand_id: UUID, db: Session = Depends(get_db)):
    """Get analytics statistics for a brand."""
    # Validate brand exists
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Count events by type
    event_counts = {}
    event_types = ['view_brand', 'view_product', 'swipe_right', 'swipe_left', 'wishlist_save', 'click_link']
    
    for event_type in event_types:
        count = db.query(BrandAnalyticsEvent).filter(
            BrandAnalyticsEvent.brand_id == brand_id,
            BrandAnalyticsEvent.event_type == event_type
        ).count()
        event_counts[event_type] = count
    
    total_events = sum(event_counts.values())
    
    return {
        "brand_id": brand_id,
        "total_events": total_events,
        "event_breakdown": event_counts
    }

@router.get("/stats/product/{product_id}")
def get_product_stats(product_id: UUID, db: Session = Depends(get_db)):
    """Get analytics statistics for a product."""
    # Validate product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Count events by type for this product
    event_counts = {}
    event_types = ['view_product', 'swipe_right', 'swipe_left', 'wishlist_save', 'click_link']
    
    for event_type in event_types:
        count = db.query(BrandAnalyticsEvent).filter(
            BrandAnalyticsEvent.product_id == product_id,
            BrandAnalyticsEvent.event_type == event_type
        ).count()
        event_counts[event_type] = count
    
    total_events = sum(event_counts.values())
    
    return {
        "product_id": product_id,
        "total_events": total_events,
        "event_breakdown": event_counts
    } 