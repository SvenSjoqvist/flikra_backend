#!/usr/bin/env python3
"""
Script to create sample swipe data for testing recommendations.
"""

import sys
sys.path.insert(0, '.')

from app.db import SessionLocal, check_database_connection
from app.models import User, Product, Swipe
import random

def create_sample_swipes():
    """Create sample swipe data for testing."""
    print("🚀 Creating sample swipe data...")
    
    if not check_database_connection():
        print("❌ Cannot connect to database.")
        return False
    
    db = SessionLocal()
    
    try:
        # Get all users and products
        users = db.query(User).all()
        products = db.query(Product).all()
        
        if not users or not products:
            print("❌ No users or products found. Run create_mock_data.py first.")
            return False
        
        print(f"📊 Found {len(users)} users and {len(products)} products")
        
        # Create realistic swipe patterns
        swipe_count = 0
        
        for user in users[:3]:  # First 3 users
            # Each user swipes on 60-80% of products
            products_to_swipe = random.sample(products, random.randint(6, 8))
            
            for product in products_to_swipe:
                # Check if swipe already exists
                existing_swipe = db.query(Swipe).filter(
                    Swipe.user_id == user.id,
                    Swipe.product_id == product.id
                ).first()
                
                if existing_swipe:
                    continue
                
                # Simulate preferences:
                # - Higher chance to like T-Shirts, Jeans, Sneakers
                # - Lower chance to like formal wear
                # - Women prefer dresses, men prefer shirts
                
                like_probability = 0.4  # Base probability
                
                if product.category in ['T-Shirts', 'Jeans', 'Sneakers']:
                    like_probability = 0.7
                elif product.category in ['Dresses'] and 'sarah' in user.email:
                    like_probability = 0.8
                elif product.category in ['Shirts'] and 'john' in user.email:
                    like_probability = 0.8
                elif product.category in ['Accessories']:
                    like_probability = 0.6
                elif product.category in ['Jackets']:
                    like_probability = 0.5
                
                # Decide direction
                direction = "right" if random.random() < like_probability else "left"
                
                # Create swipe
                swipe = Swipe(
                    user_id=user.id,
                    product_id=product.id,
                    brand_id=product.brand_id,
                    direction=direction
                )
                
                db.add(swipe)
                swipe_count += 1
        
        db.commit()
        
        # Get stats
        total_swipes = db.query(Swipe).count()
        right_swipes = db.query(Swipe).filter(Swipe.direction == "right").count()
        left_swipes = db.query(Swipe).filter(Swipe.direction == "left").count()
        
        print(f"✅ Created {swipe_count} new swipes")
        print(f"📊 Total swipes in database: {total_swipes}")
        print(f"   👍 Right swipes: {right_swipes}")
        print(f"   👎 Left swipes: {left_swipes}")
        print(f"   📈 Like rate: {(right_swipes/total_swipes*100):.1f}%")
        print("\n🎉 Sample swipe data created!")
        print("💡 Now you can test recommendations at:")
        print("   🔗 GET /recommendations/{user_id}")
        print("   🔗 GET /recommendations/{user_id}/simple")
        
        # Show some user IDs for testing
        print(f"\n👥 Sample user IDs for testing:")
        for user in users[:3]:
            user_swipes = db.query(Swipe).filter(Swipe.user_id == user.id).count()
            user_likes = db.query(Swipe).filter(Swipe.user_id == user.id, Swipe.direction == "right").count()
            print(f"   📧 {user.email}: {user.id} ({user_likes} likes, {user_swipes} total swipes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating swipe data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_swipes() 