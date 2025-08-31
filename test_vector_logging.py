#!/usr/bin/env python3
"""
Test script to demonstrate vector recommendation logging
"""
import sys
import os
import logging
from uuid import UUID
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.models import Product, User, Swipe
from app.services.recommendations import RecommendationsService

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def test_vector_recommendations_with_logging():
    """Test vector recommendations with detailed logging"""
    
    db = next(get_db())
    recommendations_service = RecommendationsService(db)
    
    try:
        # Use the specific user ID
        user_id = UUID("f4839b02-e244-4700-b1dd-bad4f664aeff")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"❌ User {user_id} not found in database")
            return
        
        print(f"👤 Testing with user: {user.id}")
        
        # Check user's swipe history
        swipes = db.query(Swipe).filter(Swipe.user_id == user.id).all()
        liked_swipes = [s for s in swipes if s.action == "right"]
        
        print(f"📊 User has {len(swipes)} total swipes ({len(liked_swipes)} likes)")
        
        if len(liked_swipes) == 0:
            print("⚠️ User has no liked products, creating some test swipes...")
            
            # Create some test swipes for demonstration (avoid duplicates)
            existing_product_ids = {s.product_id for s in swipes}
            products = db.query(Product).filter(~Product.id.in_(existing_product_ids)).limit(5).all()
            
            for product in products:
                swipe = Swipe(
                    user_id=user.id,
                    product_id=product.id,
                    action="right"
                )
                db.add(swipe)
            db.commit()
            print(f"✅ Created {len(products)} test likes")
        
        # Get vector recommendations
        print("\n" + "="*60)
        print("🚀 GETTING VECTOR RECOMMENDATIONS")
        print("="*60)
        
        recommendations = recommendations_service.get_vector_recommendations(
            user_id=user.id,
            limit=5,
            weights={
                'image_similarity': 0.6,
                'text_similarity': 0.4
            }
        )
        
        print("\n" + "="*60)
        print("📋 FINAL RECOMMENDATIONS")
        print("="*60)
        
        for i, rec in enumerate(recommendations):
            product = rec['product']
            score = rec['score']
            reason = rec['reason']
            
            print(f"\n🏆 Recommendation {i+1}:")
            print(f"   Product: {product.name}")
            print(f"   Category: {product.category}")
            print(f"   Brand: {product.brand.name if product.brand else 'Unknown'}")
            print(f"   Similarity Score: {score:.4f}")
            print(f"   Reason: {reason}")
            print(f"   Vectors: Image={bool(product.image_vector)}, Text={bool(product.text_vector)}, Combined={bool(product.combined_vector)}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_vector_recommendations_with_logging() 