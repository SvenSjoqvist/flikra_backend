#!/usr/bin/env python3
"""
Debug script to check user swipe status and available products for recommendations
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append('app')

from app.db import get_db
from app.models import Swipe, Product
from uuid import UUID

def debug_user_swipes(user_id_str: str):
    """Debug user swipes and available products"""
    try:
        user_id = UUID(user_id_str)
        print(f"🔍 Debugging user: {user_id}")
        
        # Get database session
        db = next(get_db())
        
        # Count total products
        total_products = db.query(Product).count()
        print(f"📦 Total products in database: {total_products}")
        
        # Count products with vectors
        products_with_vectors = db.query(Product).filter(
            Product.combined_vector.isnot(None)
        ).count()
        print(f"🔢 Products with vectors: {products_with_vectors}")
        
        # Get user's swipes
        user_swipes = db.query(Swipe).filter(Swipe.user_id == user_id).all()
        print(f"👆 User swipes: {len(user_swipes)}")
        
        # Count by action
        right_swipes = [s for s in user_swipes if s.action == "right"]
        left_swipes = [s for s in user_swipes if s.action == "left"]
        print(f"   - Right swipes: {len(right_swipes)}")
        print(f"   - Left swipes: {len(left_swipes)}")
        
        # Get swiped product IDs
        swiped_ids = {s.product_id for s in user_swipes}
        print(f"🚫 Swiped product IDs: {len(swiped_ids)}")
        
        # Check how many products are available for recommendations
        available_products = db.query(Product).filter(
            Product.combined_vector.isnot(None),
            ~Product.id.in_(swiped_ids)
        ).count()
        print(f"✅ Available products for recommendations: {available_products}")
        
        # Check if user has swiped all products
        if available_products == 0:
            print("⚠️  User has swiped ALL available products!")
            print("💡 This is why they're getting 0 recommendations")
            
            # Show some swiped products
            print("\n📋 Sample of swiped products:")
            for i, swipe in enumerate(user_swipes[:5]):
                product = db.query(Product).filter(Product.id == swipe.product_id).first()
                if product:
                    print(f"   {i+1}. {product.name} ({swipe.action})")
        else:
            print(f"🎯 User can still get {available_products} recommendations")
        
        # Check vector coverage
        print(f"\n📊 Vector Coverage:")
        print(f"   - Total products: {total_products}")
        print(f"   - With vectors: {products_with_vectors}")
        print(f"   - Coverage: {(products_with_vectors/total_products)*100:.1f}%")
        
        return {
            'total_products': total_products,
            'products_with_vectors': products_with_vectors,
            'user_swipes': len(user_swipes),
            'available_for_recommendations': available_products
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_user_swipes.py <user_id>")
        print("Example: python debug_user_swipes.py 0178581f-5cac-4b09-93de-b8b174d4772d")
        sys.exit(1)
    
    user_id = sys.argv[1]
    result = debug_user_swipes(user_id)
    
    if result:
        print(f"\n🎯 Summary:")
        print(f"   - User has swiped {result['user_swipes']} products")
        print(f"   - {result['available_for_recommendations']} products available for recommendations")
        print(f"   - Vector coverage: {result['products_with_vectors']}/{result['total_products']}") 