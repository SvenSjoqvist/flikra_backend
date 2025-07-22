#!/usr/bin/env python3
"""
Script to add 5 more products using a specified image URL.
"""

import sys
sys.path.insert(0, '.')

from app.db import SessionLocal, check_database_connection
from app.models import Brand, Product
from app.utils.vectorization import generate_combined_vector

IMAGE_URL = "https://d2v5dzhdg4zhx3.cloudfront.net/web-assets/images/storypages/primary/ProductShowcasesampleimages/JPEG/Product+Showcase-1.jpg"


def add_5_more_products():
    """Add 5 more products using the specified image URL."""
    print("🚀 Adding 5 more products with the specified image URL...")
    
    if not check_database_connection():
        print("❌ Cannot connect to database.")
        return False
    
    db = SessionLocal()
    
    try:
        # Get all brands for products
        all_brands = db.query(Brand).all()
        
        if not all_brands:
            print("❌ No brands found! Run create_mock_data.py first.")
            return False
        
        print(f"🏢 Found {len(all_brands)} brands to assign products to")
        
        # 5 new products using the specified image
        new_products = [
            {
                "name": "Unique Sample Product 1",
                "description": "A unique sample product using the specified image.",
                "image_url": IMAGE_URL,
                "item_url": "https://example.com/shop/unique-sample-product-1",
                "color": "Crimson",
                "category": "Hats",
                "gender": "Unisex",
                "tags": ["unique", "hat", "crimson"],
                "product_metadata": {"material": "Wool", "fit": "One Size"}
            },
            {
                "name": "Unique Sample Product 2",
                "description": "A unique sample product using the specified image.",
                "image_url": IMAGE_URL,
                "item_url": "https://example.com/shop/unique-sample-product-2",
                "color": "Azure",
                "category": "Bags",
                "gender": "Unisex",
                "tags": ["unique", "bag", "azure"],
                "product_metadata": {"material": "Canvas", "fit": "Large"}
            },
            {
                "name": "Unique Sample Product 3",
                "description": "A unique sample product using the specified image.",
                "image_url": IMAGE_URL,
                "item_url": "https://example.com/shop/unique-sample-product-3",
                "color": "Emerald",
                "category": "Jackets",
                "gender": "Unisex",
                "tags": ["unique", "jacket", "emerald"],
                "product_metadata": {"material": "Leather", "fit": "Medium"}
            },
            {
                "name": "Unique Sample Product 4",
                "description": "A unique sample product using the specified image.",
                "image_url": IMAGE_URL,
                "item_url": "https://example.com/shop/unique-sample-product-4",
                "color": "Amber",
                "category": "Scarves",
                "gender": "Unisex",
                "tags": ["unique", "scarf", "amber"],
                "product_metadata": {"material": "Silk", "fit": "One Size"}
            },
            {
                "name": "Unique Sample Product 5",
                "description": "A unique sample product using the specified image.",
                "image_url": IMAGE_URL,
                "item_url": "https://example.com/shop/unique-sample-product-5",
                "color": "Onyx",
                "category": "Gloves",
                "gender": "Unisex",
                "tags": ["unique", "glove", "onyx"],
                "product_metadata": {"material": "Nylon", "fit": "Small"}
            }
        ]
        
        created_products = []
        for i, product_data in enumerate(new_products):
            # Assign to different brands cyclically
            brand = all_brands[i % len(all_brands)]
            product_data["brand_id"] = brand.id
            
            # Generate combined vector
            product_data["vector_id_combined"] = generate_combined_vector(product_data["image_url"], product_data["description"])
            
            # Check if product already exists
            existing_product = db.query(Product).filter(Product.name == product_data["name"]).first()
            if not existing_product:
                product = Product(**product_data)
                db.add(product)
                created_products.append(product)
        
        db.commit()
        print(f"✅ Created {len(created_products)} new products")
        
        # Summary
        total_brands = db.query(Brand).count()
        total_products = db.query(Product).count()
        
        print("\n🎉 5 more products added!")
        print(f"📊 Updated Database Summary:")
        print(f"   🏢 Total Brands: {total_brands}")
        print(f"   👕 Total Products: {total_products}")
        
        print("\n💡 More data for better recommendations!")
        print("🔗 Try the recommendations endpoints again!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding more products: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    add_5_more_products() 