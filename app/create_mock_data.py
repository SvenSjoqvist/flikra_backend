#!/usr/bin/env python3
"""
Script to create mock data for testing the Fashion Platform API.
"""

import sys
sys.path.insert(0, '.')

from app.db import SessionLocal, check_database_connection
from app.models import User, Brand, Product, Role, UserRole
from app.utils.auth import get_password_hash
import uuid

def create_mock_data():
    """Create mock data for testing."""
    print("🚀 Creating mock data...")
    
    # Check database connection
    if not check_database_connection():
        print("❌ Cannot connect to database.")
        return False
    
    db = SessionLocal()
    
    try:
        # Create mock users
        print("👥 Creating mock users...")
        mock_users = [
            {"email": "john@example.com", "password": "password123"},
            {"email": "sarah@example.com", "password": "password123"},
            {"email": "mike@example.com", "password": "password123"},
            {"email": "emma@example.com", "password": "password123"},
            {"email": "alex@example.com", "password": "password123"},
        ]
        
        created_users = []
        for user_data in mock_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"])
                )
                db.add(user)
                created_users.append(user)
        
        db.commit()
        print(f"✅ Created {len(created_users)} users")
        
        # Create mock brands
        print("🏢 Creating mock brands...")
        mock_brands = [
            {
                "name": "Urban Style Co.",
                "description": "Modern streetwear for the urban lifestyle",
                "website_url": "https://urbanstyle.com",
                "image_urls": ["https://example.com/urban-logo.jpg"],
                "tags": ["streetwear", "urban", "modern"]
            },
            {
                "name": "Elegant Fashion",
                "description": "Luxury fashion for sophisticated tastes",
                "website_url": "https://elegantfashion.com",
                "image_urls": ["https://example.com/elegant-logo.jpg"],
                "tags": ["luxury", "elegant", "formal"]
            },
            {
                "name": "Casual Wear Plus",
                "description": "Comfortable everyday clothing",
                "website_url": "https://casualwear.com",
                "image_urls": ["https://example.com/casual-logo.jpg"],
                "tags": ["casual", "comfortable", "everyday"]
            },
            {
                "name": "Sports Active",
                "description": "Athletic wear for active lifestyles",
                "website_url": "https://sportsactive.com",
                "image_urls": ["https://example.com/sports-logo.jpg"],
                "tags": ["sports", "athletic", "active"]
            },
            {
                "name": "Vintage Collective",
                "description": "Curated vintage and retro fashion",
                "website_url": "https://vintagecollective.com",
                "image_urls": ["https://example.com/vintage-logo.jpg"],
                "tags": ["vintage", "retro", "classic"]
            }
        ]
        
        created_brands = []
        for brand_data in mock_brands:
            # Check if brand already exists
            existing_brand = db.query(Brand).filter(Brand.name == brand_data["name"]).first()
            if not existing_brand:
                brand = Brand(**brand_data)
                db.add(brand)
                created_brands.append(brand)
        
        db.commit()
        print(f"✅ Created {len(created_brands)} brands")
        
        # Get all brands for products
        all_brands = db.query(Brand).all()
        
        # Create mock products
        print("👕 Creating mock products...")
        mock_products = [
            {
                "name": "Classic White T-Shirt",
                "description": "Premium cotton white t-shirt, perfect for any occasion",
                "image_url": "https://example.com/white-tshirt.jpg",
                "item_url": "https://example.com/shop/white-tshirt",
                "color": "White",
                "category": "T-Shirts",
                "gender": "Unisex",
                "tags": ["basic", "cotton", "classic"],
                "product_metadata": {"material": "100% Cotton", "fit": "Regular"}
            },
            {
                "name": "Slim Fit Jeans",
                "description": "Dark wash slim fit jeans with stretch comfort",
                "image_url": "https://example.com/jeans.jpg",
                "item_url": "https://example.com/shop/slim-jeans",
                "color": "Dark Blue",
                "category": "Jeans",
                "gender": "Men",
                "tags": ["denim", "slim", "stretch"],
                "product_metadata": {"material": "98% Cotton, 2% Elastane", "fit": "Slim"}
            },
            {
                "name": "Floral Summer Dress",
                "description": "Light and airy floral dress perfect for summer",
                "image_url": "https://example.com/summer-dress.jpg",
                "item_url": "https://example.com/shop/floral-dress",
                "color": "Floral",
                "category": "Dresses",
                "gender": "Women",
                "tags": ["summer", "floral", "light"],
                "product_metadata": {"material": "100% Rayon", "fit": "A-Line"}
            },
            {
                "name": "Leather Jacket",
                "description": "Genuine leather jacket with classic biker style",
                "image_url": "https://example.com/leather-jacket.jpg",
                "item_url": "https://example.com/shop/leather-jacket",
                "color": "Black",
                "category": "Jackets",
                "gender": "Unisex",
                "tags": ["leather", "biker", "classic"],
                "product_metadata": {"material": "Genuine Leather", "fit": "Regular"}
            },
            {
                "name": "Running Sneakers",
                "description": "Lightweight running shoes with excellent cushioning",
                "image_url": "https://example.com/sneakers.jpg",
                "item_url": "https://example.com/shop/running-sneakers",
                "color": "Black/White",
                "category": "Shoes",
                "gender": "Unisex",
                "tags": ["running", "athletic", "comfortable"],
                "product_metadata": {"material": "Mesh/Rubber", "type": "Athletic"}
            },
            {
                "name": "Wool Sweater",
                "description": "Cozy wool sweater for cold weather",
                "image_url": "https://example.com/wool-sweater.jpg",
                "item_url": "https://example.com/shop/wool-sweater",
                "color": "Gray",
                "category": "Sweaters",
                "gender": "Unisex",
                "tags": ["wool", "warm", "winter"],
                "product_metadata": {"material": "100% Merino Wool", "fit": "Regular"}
            },
            {
                "name": "Mini Skirt",
                "description": "Trendy mini skirt with pleated design",
                "image_url": "https://example.com/mini-skirt.jpg",
                "item_url": "https://example.com/shop/mini-skirt",
                "color": "Navy",
                "category": "Skirts",
                "gender": "Women",
                "tags": ["mini", "pleated", "trendy"],
                "product_metadata": {"material": "Polyester Blend", "fit": "A-Line"}
            },
            {
                "name": "Button-Up Shirt",
                "description": "Professional button-up shirt for business wear",
                "image_url": "https://example.com/button-shirt.jpg",
                "item_url": "https://example.com/shop/button-shirt",
                "color": "Light Blue",
                "category": "Shirts",
                "gender": "Men",
                "tags": ["formal", "business", "professional"],
                "product_metadata": {"material": "Cotton Blend", "fit": "Tailored"}
            },
            {
                "name": "Yoga Pants",
                "description": "Flexible yoga pants with moisture-wicking fabric",
                "image_url": "https://example.com/yoga-pants.jpg",
                "item_url": "https://example.com/shop/yoga-pants",
                "color": "Black",
                "category": "Activewear",
                "gender": "Women",
                "tags": ["yoga", "flexible", "athletic"],
                "product_metadata": {"material": "Spandex Blend", "fit": "Compression"}
            },
            {
                "name": "Baseball Cap",
                "description": "Classic baseball cap with adjustable strap",
                "image_url": "https://example.com/baseball-cap.jpg",
                "item_url": "https://example.com/shop/baseball-cap",
                "color": "Red",
                "category": "Accessories",
                "gender": "Unisex",
                "tags": ["cap", "adjustable", "classic"],
                "product_metadata": {"material": "Cotton Twill", "type": "Headwear"}
            }
        ]
        
        created_products = []
        for i, product_data in enumerate(mock_products):
            # Assign to different brands cyclically
            brand = all_brands[i % len(all_brands)]
            product_data["brand_id"] = brand.id
            
            # Check if product already exists
            existing_product = db.query(Product).filter(Product.name == product_data["name"]).first()
            if not existing_product:
                product = Product(**product_data)
                db.add(product)
                created_products.append(product)
        
        db.commit()
        print(f"✅ Created {len(created_products)} products")
        
        # Summary
        total_users = db.query(User).count()
        total_brands = db.query(Brand).count()
        total_products = db.query(Product).count()
        
        print("\n🎉 Mock data creation complete!")
        print(f"📊 Database Summary:")
        print(f"   👥 Users: {total_users}")
        print(f"   🏢 Brands: {total_brands}")
        print(f"   👕 Products: {total_products}")
        print("\n💡 You can now test the API with real data!")
        print("🔗 Try: http://localhost:8001/docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating mock data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    create_mock_data() 