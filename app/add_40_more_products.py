#!/usr/bin/env python3
"""
Script to add 40 more diverse mock products for better testing.
"""

import sys
sys.path.insert(0, '.')

from app.db import SessionLocal, check_database_connection
from app.models import Brand, Product
import random

def add_40_more_products():
    """Add 40 more diverse products across various categories."""
    print("🚀 Adding 40 more mock products...")
    
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
        
        # 40 more diverse products
        new_products = [
            # More T-Shirts (8 products)
            {
                "name": "Graphic Print Tee",
                "description": "Cool graphic print t-shirt with artistic design",
                "image_url": "https://example.com/graphic-tee.jpg",
                "item_url": "https://example.com/shop/graphic-tee",
                "color": "White",
                "category": "T-Shirts",
                "gender": "Unisex",
                "tags": ["graphic", "art", "creative"],
                "product_metadata": {"material": "100% Cotton", "fit": "Regular"}
            },
            {
                "name": "Striped Long Sleeve Tee",
                "description": "Classic striped long sleeve t-shirt",
                "image_url": "https://example.com/striped-tee.jpg",
                "item_url": "https://example.com/shop/striped-tee",
                "color": "Navy & White",
                "category": "T-Shirts",
                "gender": "Unisex",
                "tags": ["striped", "classic", "long-sleeve"],
                "product_metadata": {"material": "Cotton Blend", "fit": "Regular"}
            },
            {
                "name": "V-Neck Basic Tee",
                "description": "Simple v-neck t-shirt in soft cotton",
                "image_url": "https://example.com/vneck-tee.jpg",
                "item_url": "https://example.com/shop/vneck-tee",
                "color": "Gray",
                "category": "T-Shirts",
                "gender": "Women",
                "tags": ["v-neck", "basic", "soft"],
                "product_metadata": {"material": "100% Cotton", "fit": "Fitted"}
            },
            {
                "name": "Tie-Dye Tee",
                "description": "Retro tie-dye t-shirt with vibrant colors",
                "image_url": "https://example.com/tiedye-tee.jpg",
                "item_url": "https://example.com/shop/tiedye-tee",
                "color": "Multi-Color",
                "category": "T-Shirts",
                "gender": "Unisex",
                "tags": ["tie-dye", "retro", "colorful"],
                "product_metadata": {"material": "100% Cotton", "fit": "Relaxed"}
            },
            {
                "name": "Pocket Tee",
                "description": "Simple t-shirt with chest pocket",
                "image_url": "https://example.com/pocket-tee.jpg",
                "item_url": "https://example.com/shop/pocket-tee",
                "color": "Olive",
                "category": "T-Shirts",
                "gender": "Men",
                "tags": ["pocket", "casual", "simple"],
                "product_metadata": {"material": "100% Cotton", "fit": "Regular"}
            },
            {
                "name": "Oversized Tee",
                "description": "Trendy oversized t-shirt for relaxed style",
                "image_url": "https://example.com/oversized-tee.jpg",
                "item_url": "https://example.com/shop/oversized-tee",
                "color": "Pink",
                "category": "T-Shirts",
                "gender": "Women",
                "tags": ["oversized", "trendy", "relaxed"],
                "product_metadata": {"material": "Cotton Blend", "fit": "Oversized"}
            },
            {
                "name": "Logo Tee",
                "description": "Brand logo t-shirt with modern design",
                "image_url": "https://example.com/logo-tee.jpg",
                "item_url": "https://example.com/shop/logo-tee",
                "color": "Black",
                "category": "T-Shirts",
                "gender": "Unisex",
                "tags": ["logo", "brand", "modern"],
                "product_metadata": {"material": "100% Cotton", "fit": "Regular"}
            },
            {
                "name": "Ringer Tee",
                "description": "Vintage-style ringer t-shirt with contrast trim",
                "image_url": "https://example.com/ringer-tee.jpg",
                "item_url": "https://example.com/shop/ringer-tee",
                "color": "White/Red",
                "category": "T-Shirts",
                "gender": "Unisex",
                "tags": ["ringer", "vintage", "contrast"],
                "product_metadata": {"material": "100% Cotton", "fit": "Regular"}
            },

            # More Shirts (6 products)
            {
                "name": "Oxford Button-Down",
                "description": "Classic oxford button-down shirt",
                "image_url": "https://example.com/oxford-shirt.jpg",
                "item_url": "https://example.com/shop/oxford-shirt",
                "color": "Light Blue",
                "category": "Shirts",
                "gender": "Men",
                "tags": ["oxford", "button-down", "classic"],
                "product_metadata": {"material": "100% Cotton", "fit": "Regular"}
            },
            {
                "name": "Denim Shirt",
                "description": "Casual denim shirt for everyday wear",
                "image_url": "https://example.com/denim-shirt.jpg",
                "item_url": "https://example.com/shop/denim-shirt",
                "color": "Blue Denim",
                "category": "Shirts",
                "gender": "Unisex",
                "tags": ["denim", "casual", "everyday"],
                "product_metadata": {"material": "100% Cotton Denim", "fit": "Regular"}
            },
            {
                "name": "Silk Blouse",
                "description": "Elegant silk blouse for professional wear",
                "image_url": "https://example.com/silk-blouse.jpg",
                "item_url": "https://example.com/shop/silk-blouse",
                "color": "Cream",
                "category": "Shirts",
                "gender": "Women",
                "tags": ["silk", "elegant", "professional"],
                "product_metadata": {"material": "100% Silk", "fit": "Fitted"}
            },
            {
                "name": "Linen Shirt",
                "description": "Breathable linen shirt for summer",
                "image_url": "https://example.com/linen-shirt.jpg",
                "item_url": "https://example.com/shop/linen-shirt",
                "color": "White",
                "category": "Shirts",
                "gender": "Unisex",
                "tags": ["linen", "breathable", "summer"],
                "product_metadata": {"material": "100% Linen", "fit": "Relaxed"}
            },
            {
                "name": "Plaid Shirt",
                "description": "Traditional plaid pattern shirt",
                "image_url": "https://example.com/plaid-shirt.jpg",
                "item_url": "https://example.com/shop/plaid-shirt",
                "color": "Red Plaid",
                "category": "Shirts",
                "gender": "Unisex",
                "tags": ["plaid", "traditional", "pattern"],
                "product_metadata": {"material": "Cotton Flannel", "fit": "Regular"}
            },
            {
                "name": "Band Collar Shirt",
                "description": "Modern band collar shirt without traditional collar",
                "image_url": "https://example.com/band-collar.jpg",
                "item_url": "https://example.com/shop/band-collar",
                "color": "Navy",
                "category": "Shirts",
                "gender": "Men",
                "tags": ["band-collar", "modern", "minimal"],
                "product_metadata": {"material": "Cotton Blend", "fit": "Slim"}
            },

            # More Jeans (5 products)
            {
                "name": "High-Waisted Jeans",
                "description": "Trendy high-waisted denim jeans",
                "image_url": "https://example.com/high-waisted.jpg",
                "item_url": "https://example.com/shop/high-waisted",
                "color": "Dark Blue",
                "category": "Jeans",
                "gender": "Women",
                "tags": ["high-waisted", "trendy", "denim"],
                "product_metadata": {"material": "98% Cotton, 2% Elastane", "fit": "High-Rise"}
            },
            {
                "name": "Bootcut Jeans",
                "description": "Classic bootcut jeans with slight flare",
                "image_url": "https://example.com/bootcut.jpg",
                "item_url": "https://example.com/shop/bootcut",
                "color": "Medium Blue",
                "category": "Jeans",
                "gender": "Unisex",
                "tags": ["bootcut", "classic", "flare"],
                "product_metadata": {"material": "100% Cotton Denim", "fit": "Bootcut"}
            },
            {
                "name": "Ripped Jeans",
                "description": "Distressed jeans with stylish rips",
                "image_url": "https://example.com/ripped-jeans.jpg",
                "item_url": "https://example.com/shop/ripped-jeans",
                "color": "Light Blue",
                "category": "Jeans",
                "gender": "Unisex",
                "tags": ["ripped", "distressed", "edgy"],
                "product_metadata": {"material": "95% Cotton, 5% Elastane", "fit": "Slim"}
            },
            {
                "name": "Mom Jeans",
                "description": "Vintage-inspired mom jeans with high waist",
                "image_url": "https://example.com/mom-jeans.jpg",
                "item_url": "https://example.com/shop/mom-jeans",
                "color": "Vintage Blue",
                "category": "Jeans",
                "gender": "Women",
                "tags": ["mom-jeans", "vintage", "high-waist"],
                "product_metadata": {"material": "100% Cotton Denim", "fit": "Relaxed"}
            },
            {
                "name": "Black Jeans",
                "description": "Versatile black denim jeans",
                "image_url": "https://example.com/black-jeans.jpg",
                "item_url": "https://example.com/shop/black-jeans",
                "color": "Black",
                "category": "Jeans",
                "gender": "Unisex",
                "tags": ["black", "versatile", "denim"],
                "product_metadata": {"material": "95% Cotton, 5% Elastane", "fit": "Slim"}
            },

            # More Dresses (5 products)
            {
                "name": "Sundress",
                "description": "Light and airy sundress perfect for summer",
                "image_url": "https://example.com/sundress.jpg",
                "item_url": "https://example.com/shop/sundress",
                "color": "Yellow",
                "category": "Dresses",
                "gender": "Women",
                "tags": ["sundress", "summer", "light"],
                "product_metadata": {"material": "Cotton Blend", "fit": "A-Line"}
            },
            {
                "name": "Wrap Dress",
                "description": "Flattering wrap dress with tie waist",
                "image_url": "https://example.com/wrap-dress.jpg",
                "item_url": "https://example.com/shop/wrap-dress",
                "color": "Floral Print",
                "category": "Dresses",
                "gender": "Women",
                "tags": ["wrap", "flattering", "tie-waist"],
                "product_metadata": {"material": "Viscose", "fit": "Wrap"}
            },
            {
                "name": "Shift Dress",
                "description": "Simple shift dress for professional occasions",
                "image_url": "https://example.com/shift-dress.jpg",
                "item_url": "https://example.com/shop/shift-dress",
                "color": "Navy",
                "category": "Dresses",
                "gender": "Women",
                "tags": ["shift", "professional", "simple"],
                "product_metadata": {"material": "Polyester Blend", "fit": "Straight"}
            },
            {
                "name": "Mini Dress",
                "description": "Trendy mini dress for night out",
                "image_url": "https://example.com/mini-dress.jpg",
                "item_url": "https://example.com/shop/mini-dress",
                "color": "Red",
                "category": "Dresses",
                "gender": "Women",
                "tags": ["mini", "trendy", "night-out"],
                "product_metadata": {"material": "Spandex Blend", "fit": "Bodycon"}
            },
            {
                "name": "Midi Dress",
                "description": "Versatile midi dress for any occasion",
                "image_url": "https://example.com/midi-dress.jpg",
                "item_url": "https://example.com/shop/midi-dress",
                "color": "Green",
                "category": "Dresses",
                "gender": "Women",
                "tags": ["midi", "versatile", "occasion"],
                "product_metadata": {"material": "Cotton Blend", "fit": "A-Line"}
            },

            # More Shoes (6 products)
            {
                "name": "Running Shoes",
                "description": "Comfortable running shoes with cushioned sole",
                "image_url": "https://example.com/running-shoes.jpg",
                "item_url": "https://example.com/shop/running-shoes",
                "color": "Black/White",
                "category": "Shoes",
                "gender": "Unisex",
                "tags": ["running", "comfortable", "cushioned"],
                "product_metadata": {"material": "Mesh/Rubber", "type": "Athletic"}
            },
            {
                "name": "Dress Shoes",
                "description": "Formal dress shoes for business occasions",
                "image_url": "https://example.com/dress-shoes.jpg",
                "item_url": "https://example.com/shop/dress-shoes",
                "color": "Black",
                "category": "Shoes",
                "gender": "Men",
                "tags": ["dress", "formal", "business"],
                "product_metadata": {"material": "Leather", "type": "Formal"}
            },
            {
                "name": "Ballet Flats",
                "description": "Classic ballet flats for everyday comfort",
                "image_url": "https://example.com/ballet-flats.jpg",
                "item_url": "https://example.com/shop/ballet-flats",
                "color": "Nude",
                "category": "Shoes",
                "gender": "Women",
                "tags": ["ballet", "flats", "comfort"],
                "product_metadata": {"material": "Leather", "type": "Casual"}
            },
            {
                "name": "Ankle Boots",
                "description": "Stylish ankle boots with low heel",
                "image_url": "https://example.com/ankle-boots.jpg",
                "item_url": "https://example.com/shop/ankle-boots",
                "color": "Tan",
                "category": "Shoes",
                "gender": "Women",
                "tags": ["ankle", "boots", "heel"],
                "product_metadata": {"material": "Suede", "type": "Boots"}
            },
            {
                "name": "Loafers",
                "description": "Comfortable slip-on loafers",
                "image_url": "https://example.com/loafers.jpg",
                "item_url": "https://example.com/shop/loafers",
                "color": "Brown",
                "category": "Shoes",
                "gender": "Men",
                "tags": ["loafers", "slip-on", "comfortable"],
                "product_metadata": {"material": "Leather", "type": "Casual"}
            },
            {
                "name": "Sandals",
                "description": "Open-toe sandals for summer weather",
                "image_url": "https://example.com/sandals.jpg",
                "item_url": "https://example.com/shop/sandals",
                "color": "Gold",
                "category": "Shoes",
                "gender": "Women",
                "tags": ["sandals", "summer", "open-toe"],
                "product_metadata": {"material": "Synthetic", "type": "Casual"}
            },

            # More Accessories (5 products)
            {
                "name": "Baseball Cap",
                "description": "Classic baseball cap with adjustable strap",
                "image_url": "https://example.com/baseball-cap.jpg",
                "item_url": "https://example.com/shop/baseball-cap",
                "color": "Navy",
                "category": "Accessories",
                "gender": "Unisex",
                "tags": ["cap", "baseball", "adjustable"],
                "product_metadata": {"material": "Cotton Twill", "type": "Hat"}
            },
            {
                "name": "Crossbody Bag",
                "description": "Compact crossbody bag for hands-free carrying",
                "image_url": "https://example.com/crossbody-bag.jpg",
                "item_url": "https://example.com/shop/crossbody-bag",
                "color": "Black",
                "category": "Accessories",
                "gender": "Women",
                "tags": ["crossbody", "bag", "hands-free"],
                "product_metadata": {"material": "Synthetic Leather", "type": "Bag"}
            },
            {
                "name": "Sunglasses",
                "description": "UV protection sunglasses with stylish frame",
                "image_url": "https://example.com/sunglasses.jpg",
                "item_url": "https://example.com/shop/sunglasses",
                "color": "Black",
                "category": "Accessories",
                "gender": "Unisex",
                "tags": ["sunglasses", "uv-protection", "stylish"],
                "product_metadata": {"material": "Plastic/Glass", "type": "Eyewear"}
            },
            {
                "name": "Watch",
                "description": "Minimalist watch with leather strap",
                "image_url": "https://example.com/watch.jpg",
                "item_url": "https://example.com/shop/watch",
                "color": "Silver",
                "category": "Accessories",
                "gender": "Unisex",
                "tags": ["watch", "minimalist", "leather"],
                "product_metadata": {"material": "Stainless Steel/Leather", "type": "Timepiece"}
            },
            {
                "name": "Backpack",
                "description": "Spacious backpack for daily use",
                "image_url": "https://example.com/backpack.jpg",
                "item_url": "https://example.com/shop/backpack",
                "color": "Gray",
                "category": "Accessories",
                "gender": "Unisex",
                "tags": ["backpack", "spacious", "daily"],
                "product_metadata": {"material": "Canvas", "type": "Bag"}
            },

            # More Activewear (5 products)
            {
                "name": "Yoga Pants",
                "description": "Flexible yoga pants for workouts",
                "image_url": "https://example.com/yoga-pants.jpg",
                "item_url": "https://example.com/shop/yoga-pants",
                "color": "Black",
                "category": "Activewear",
                "gender": "Women",
                "tags": ["yoga", "flexible", "workout"],
                "product_metadata": {"material": "Spandex Blend", "fit": "Compression"}
            },
            {
                "name": "Tank Top",
                "description": "Breathable tank top for gym sessions",
                "image_url": "https://example.com/tank-top.jpg",
                "item_url": "https://example.com/shop/tank-top",
                "color": "White",
                "category": "Activewear",
                "gender": "Unisex",
                "tags": ["tank", "breathable", "gym"],
                "product_metadata": {"material": "Polyester Blend", "fit": "Regular"}
            },
            {
                "name": "Joggers",
                "description": "Comfortable joggers for casual wear",
                "image_url": "https://example.com/joggers.jpg",
                "item_url": "https://example.com/shop/joggers",
                "color": "Gray",
                "category": "Activewear",
                "gender": "Unisex",
                "tags": ["joggers", "comfortable", "casual"],
                "product_metadata": {"material": "Cotton Blend", "fit": "Relaxed"}
            },
            {
                "name": "Hoodie",
                "description": "Cozy hoodie for post-workout comfort",
                "image_url": "https://example.com/hoodie.jpg",
                "item_url": "https://example.com/shop/hoodie",
                "color": "Navy",
                "category": "Activewear",
                "gender": "Unisex",
                "tags": ["hoodie", "cozy", "post-workout"],
                "product_metadata": {"material": "Cotton Fleece", "fit": "Regular"}
            },
            {
                "name": "Windbreaker",
                "description": "Light windbreaker jacket for outdoor activities",
                "image_url": "https://example.com/windbreaker.jpg",
                "item_url": "https://example.com/shop/windbreaker",
                "color": "Blue",
                "category": "Activewear",
                "gender": "Unisex",
                "tags": ["windbreaker", "outdoor", "light"],
                "product_metadata": {"material": "Nylon", "fit": "Regular"}
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
        
        print("\n🎉 40 more products added!")
        print(f"📊 Updated Database Summary:")
        print(f"   🏢 Total Brands: {total_brands}")
        print(f"   👕 Total Products: {total_products}")
        
        # Category breakdown
        categories = db.query(Product.category, db.func.count(Product.id)).group_by(Product.category).all()
        print(f"\n📈 Products by Category:")
        for category, count in categories:
            print(f"   {category}: {count} products")
        
        print("\n💡 Much more data for better recommendations!")
        print("🔗 Try the recommendations endpoints again!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding more products: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    add_40_more_products() 