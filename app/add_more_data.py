#!/usr/bin/env python3
"""
Script to add more sample data for better recommendations.
"""

import sys
sys.path.insert(0, '.')

from app.db import SessionLocal, check_database_connection
from app.models import Brand, Product
import random

def add_more_data():
    """Add more brands and products for better recommendations."""
    print("🚀 Adding more sample data...")
    
    if not check_database_connection():
        print("❌ Cannot connect to database.")
        return False
    
    db = SessionLocal()
    
    try:
        # Add more brands
        print("🏢 Adding more brands...")
        new_brands = [
            {
                "name": "Premium Threads",
                "description": "High-quality fashion for discerning customers",
                "website_url": "https://premiumthreads.com",
                "image_urls": ["https://example.com/premium-logo.jpg"],
                "tags": ["premium", "quality", "luxury"]
            },
            {
                "name": "Street Culture",
                "description": "Urban streetwear and hip-hop fashion",
                "website_url": "https://streetculture.com",
                "image_urls": ["https://example.com/street-logo.jpg"],
                "tags": ["streetwear", "hip-hop", "urban"]
            },
            {
                "name": "Eco Fashion",
                "description": "Sustainable and eco-friendly clothing",
                "website_url": "https://ecofashion.com",
                "image_urls": ["https://example.com/eco-logo.jpg"],
                "tags": ["sustainable", "eco-friendly", "organic"]
            },
            {
                "name": "Quick Fit",
                "description": "Fast fashion for busy lifestyles",
                "website_url": "https://quickfit.com",
                "image_urls": ["https://example.com/quick-logo.jpg"],
                "tags": ["fast-fashion", "affordable", "trendy"]
            }
        ]
        
        created_brands = []
        for brand_data in new_brands:
            existing_brand = db.query(Brand).filter(Brand.name == brand_data["name"]).first()
            if not existing_brand:
                brand = Brand(**brand_data)
                db.add(brand)
                created_brands.append(brand)
        
        db.commit()
        print(f"✅ Created {len(created_brands)} new brands")
        
        # Get all brands for products
        all_brands = db.query(Brand).all()
        
        # Add more products
        print("👕 Adding more products...")
        new_products = [
            # More T-Shirts
            {
                "name": "Vintage Rock Band Tee",
                "description": "Classic rock band t-shirt with vintage print",
                "image_url": "https://example.com/rock-tee.jpg",
                "item_url": "https://example.com/shop/rock-tee",
                "color": "Black",
                "category": "T-Shirts",
                "gender": "Unisex",
                "tags": ["vintage", "rock", "band"],
                "product_metadata": {"material": "100% Cotton", "fit": "Relaxed"}
            },
            {
                "name": "Organic Cotton Tee",
                "description": "Eco-friendly organic cotton t-shirt",
                "image_url": "https://example.com/organic-tee.jpg",
                "item_url": "https://example.com/shop/organic-tee",
                "color": "Natural",
                "category": "T-Shirts",
                "gender": "Unisex",
                "tags": ["organic", "eco-friendly", "sustainable"],
                "product_metadata": {"material": "100% Organic Cotton", "fit": "Regular"}
            },
            # More Shirts
            {
                "name": "Casual Flannel Shirt",
                "description": "Comfortable flannel shirt for casual wear",
                "image_url": "https://example.com/flannel.jpg",
                "item_url": "https://example.com/shop/flannel",
                "color": "Red Plaid",
                "category": "Shirts",
                "gender": "Unisex",
                "tags": ["flannel", "casual", "plaid"],
                "product_metadata": {"material": "Cotton Flannel", "fit": "Regular"}
            },
            {
                "name": "Polo Shirt",
                "description": "Classic polo shirt for smart casual look",
                "image_url": "https://example.com/polo.jpg",
                "item_url": "https://example.com/shop/polo",
                "color": "Navy",
                "category": "Shirts",
                "gender": "Men",
                "tags": ["polo", "smart-casual", "classic"],
                "product_metadata": {"material": "Cotton Pique", "fit": "Regular"}
            },
            {
                "name": "Hawaiian Print Shirt",
                "description": "Tropical Hawaiian print shirt",
                "image_url": "https://example.com/hawaiian.jpg",
                "item_url": "https://example.com/shop/hawaiian",
                "color": "Tropical Print",
                "category": "Shirts",
                "gender": "Men",
                "tags": ["hawaiian", "tropical", "vacation"],
                "product_metadata": {"material": "Rayon", "fit": "Relaxed"}
            },
            # More Jeans
            {
                "name": "Relaxed Fit Jeans",
                "description": "Comfortable relaxed fit denim jeans",
                "image_url": "https://example.com/relaxed-jeans.jpg",
                "item_url": "https://example.com/shop/relaxed-jeans",
                "color": "Light Blue",
                "category": "Jeans",
                "gender": "Unisex",
                "tags": ["relaxed", "comfortable", "casual"],
                "product_metadata": {"material": "100% Cotton Denim", "fit": "Relaxed"}
            },
            {
                "name": "Skinny Jeans",
                "description": "Trendy skinny fit jeans",
                "image_url": "https://example.com/skinny-jeans.jpg",
                "item_url": "https://example.com/shop/skinny-jeans",
                "color": "Black",
                "category": "Jeans",
                "gender": "Women",
                "tags": ["skinny", "trendy", "fitted"],
                "product_metadata": {"material": "95% Cotton, 5% Elastane", "fit": "Skinny"}
            },
            # More Dresses
            {
                "name": "Maxi Dress",
                "description": "Elegant long maxi dress",
                "image_url": "https://example.com/maxi-dress.jpg",
                "item_url": "https://example.com/shop/maxi-dress",
                "color": "Burgundy",
                "category": "Dresses",
                "gender": "Women",
                "tags": ["maxi", "elegant", "long"],
                "product_metadata": {"material": "Polyester Blend", "fit": "Flowing"}
            },
            {
                "name": "Cocktail Dress",
                "description": "Stylish cocktail dress for evening events",
                "image_url": "https://example.com/cocktail-dress.jpg",
                "item_url": "https://example.com/shop/cocktail-dress",
                "color": "Black",
                "category": "Dresses",
                "gender": "Women",
                "tags": ["cocktail", "evening", "elegant"],
                "product_metadata": {"material": "Silk Blend", "fit": "Body-con"}
            },
            # More Sneakers/Shoes
            {
                "name": "High-Top Sneakers",
                "description": "Classic high-top canvas sneakers",
                "image_url": "https://example.com/high-tops.jpg",
                "item_url": "https://example.com/shop/high-tops",
                "color": "White",
                "category": "Shoes",
                "gender": "Unisex",
                "tags": ["high-top", "canvas", "classic"],
                "product_metadata": {"material": "Canvas/Rubber", "type": "Casual"}
            },
            {
                "name": "Leather Boots",
                "description": "Durable leather boots for all weather",
                "image_url": "https://example.com/boots.jpg",
                "item_url": "https://example.com/shop/boots",
                "color": "Brown",
                "category": "Shoes",
                "gender": "Unisex",
                "tags": ["leather", "boots", "durable"],
                "product_metadata": {"material": "Genuine Leather", "type": "Boots"}
            },
            # More Accessories
            {
                "name": "Leather Belt",
                "description": "Classic leather belt with metal buckle",
                "image_url": "https://example.com/belt.jpg",
                "item_url": "https://example.com/shop/belt",
                "color": "Black",
                "category": "Accessories",
                "gender": "Unisex",
                "tags": ["leather", "belt", "classic"],
                "product_metadata": {"material": "Genuine Leather", "type": "Belt"}
            },
            {
                "name": "Wool Scarf",
                "description": "Warm wool scarf for winter",
                "image_url": "https://example.com/scarf.jpg",
                "item_url": "https://example.com/shop/scarf",
                "color": "Gray",
                "category": "Accessories",
                "gender": "Unisex",
                "tags": ["wool", "winter", "warm"],
                "product_metadata": {"material": "100% Wool", "type": "Scarf"}
            },
            # More Activewear
            {
                "name": "Sports Bra",
                "description": "High-support sports bra for workouts",
                "image_url": "https://example.com/sports-bra.jpg",
                "item_url": "https://example.com/shop/sports-bra",
                "color": "Pink",
                "category": "Activewear",
                "gender": "Women",
                "tags": ["sports", "workout", "support"],
                "product_metadata": {"material": "Spandex Blend", "fit": "Compression"}
            },
            {
                "name": "Athletic Shorts",
                "description": "Lightweight athletic shorts",
                "image_url": "https://example.com/athletic-shorts.jpg",
                "item_url": "https://example.com/shop/athletic-shorts",
                "color": "Blue",
                "category": "Activewear",
                "gender": "Men",
                "tags": ["athletic", "shorts", "lightweight"],
                "product_metadata": {"material": "Polyester Blend", "fit": "Regular"}
            }
        ]
        
        created_products = []
        for i, product_data in enumerate(new_products):
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
        print(f"✅ Created {len(created_products)} new products")
        
        # Summary
        total_brands = db.query(Brand).count()
        total_products = db.query(Product).count()
        
        print("\n🎉 More sample data added!")
        print(f"📊 Updated Database Summary:")
        print(f"   🏢 Total Brands: {total_brands}")
        print(f"   👕 Total Products: {total_products}")
        print("\n💡 Now you have more products for recommendations!")
        print("🔗 Try the recommendations endpoints again!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding more data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    add_more_data() 