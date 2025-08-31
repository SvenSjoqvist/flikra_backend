#!/usr/bin/env python3
"""
Debug script to check user and brand membership status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.models import User, BrandMember, Brand
from sqlalchemy.orm import Session

def debug_user_brand_access(email: str):
    """Debug a user's brand access"""
    db = next(get_db())
    
    print(f"🔍 Debugging user: {email}")
    print("=" * 50)
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("❌ User not found")
        return
    
    print(f"✅ User found: {user.id}")
    print(f"   Name: {user.name}")
    print(f"   Email: {user.email}")
    print(f"   Has password: {'Yes' if user.password_hash else 'No'}")
    print(f"   Created: {user.created_at}")
    
    # Check brand memberships
    brand_members = db.query(BrandMember).filter(BrandMember.user_id == user.id).all()
    print(f"\n📋 Brand Memberships: {len(brand_members)}")
    
    if not brand_members:
        print("❌ No brand memberships found")
        return
    
    for i, bm in enumerate(brand_members, 1):
        print(f"\n  {i}. Brand Member ID: {bm.id}")
        print(f"     Role: {bm.role}")
        print(f"     Status: {bm.status}")
        print(f"     Created: {bm.created_at}")
        
        # Get brand info
        brand = db.query(Brand).filter(Brand.id == bm.brand_id).first()
        if brand:
            print(f"     Brand: {brand.name} (ID: {brand.id})")
            print(f"     Brand Status: {brand.status}")
            print(f"     Industry: {brand.industry}")
        else:
            print(f"     ❌ Brand not found (ID: {bm.brand_id})")
    
    # Check active memberships specifically
    active_memberships = db.query(BrandMember).filter(
        BrandMember.user_id == user.id,
        BrandMember.status == "active"
    ).all()
    
    print(f"\n🟢 Active Memberships: {len(active_memberships)}")
    for bm in active_memberships:
        brand = db.query(Brand).filter(Brand.id == bm.brand_id).first()
        print(f"   - {brand.name if brand else 'Unknown Brand'} (Role: {bm.role})")

def list_all_users():
    """List all users with their brand access"""
    db = next(get_db())
    
    print("👥 All Users:")
    print("=" * 50)
    
    users = db.query(User).all()
    for user in users:
        brand_members = db.query(BrandMember).filter(BrandMember.user_id == user.id).all()
        active_count = len([bm for bm in brand_members if bm.status == "active"])
        
        print(f"  {user.email} - {active_count} active memberships")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
        debug_user_brand_access(email)
    else:
        list_all_users()
        print("\nUsage: python debug_user_brand.py <email>") 