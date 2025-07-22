#!/usr/bin/env python3
"""
Test script to simulate a user swiping on all products.
This helps test the "all products swiped" functionality.
"""

import sys
sys.path.insert(0, '.')

from app.db import SessionLocal, check_database_connection
from app.models import User, Product, Swipe
import random
from datetime import datetime

def create_test_user_and_swipe_all():
    """Create a test user and have them swipe on all products."""
    print("🧪 Creating test user who will swipe on all products...")
    
    if not check_database_connection():
        print("❌ Cannot connect to database.")
        return False
    
    db = SessionLocal()
    
    try:
        # Create a test user
        test_user = User(
            email="test_swiper@example.com",
            password_hash="dummy_hash_for_testing"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
        
        # Get all products
        all_products = db.query(Product).all()
        print(f"📦 Found {len(all_products)} products to swipe on")
        
        if not all_products:
            print("❌ No products found! Run create_mock_data.py first.")
            return False
        
        # Create swipes for all products (mix of likes and dislikes)
        swipes_created = 0
        for product in all_products:
            # 70% chance of liking, 30% chance of disliking
            direction = "right" if random.random() < 0.7 else "left"
            
            swipe = Swipe(
                user_id=test_user.id,
                product_id=product.id,
                brand_id=product.brand_id,
                direction=direction,
                timestamp=datetime.utcnow()
            )
            db.add(swipe)
            swipes_created += 1
        
        db.commit()
        
        # Get final stats
        total_likes = db.query(Swipe).filter(
            Swipe.user_id == test_user.id,
            Swipe.direction == "right"
        ).count()
        
        total_dislikes = db.query(Swipe).filter(
            Swipe.user_id == test_user.id,
            Swipe.direction == "left"
        ).count()
        
        print(f"\n🎉 Test user has swiped on ALL products!")
        print(f"📊 Swipe Summary:")
        print(f"   👍 Likes: {total_likes}")
        print(f"   👎 Dislikes: {total_dislikes}")
        print(f"   📱 Total Swipes: {swipes_created}")
        print(f"   💚 Like Rate: {round((total_likes / swipes_created) * 100, 1)}%")
        
        print(f"\n🧪 Test the following endpoints:")
        print(f"   📍 GET /recommendations/{test_user.id}")
        print(f"   📍 GET /recommendations/{test_user.id}/simple")
        print(f"   📍 GET /recommendations/{test_user.id}/status")
        
        print(f"\n🔗 Try in your browser:")
        print(f"   http://localhost:8001/recommendations/{test_user.id}/simple")
        print(f"   http://localhost:8001/recommendations/{test_user.id}/status")
        
        return test_user.id
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    user_id = create_test_user_and_swipe_all()
    if user_id:
        print(f"\n✨ Test user ID: {user_id}")
        print("🚀 Now test the recommendations endpoints to see the 'all swiped' responses!") 