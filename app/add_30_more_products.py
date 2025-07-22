#!/usr/bin/env python3
"""
Script to add 30 individually unique products using specified images.
"""

import sys
sys.path.insert(0, '.')

from app.db import SessionLocal, check_database_connection
from app.models import Brand, Product
from app.utils.vectorization import generate_combined_vector

# Image URLs (will cycle if more products than URLs)
IMAGE_URLS = [
    "https://img.kwcdn.com/product/open/7bfcbaf35e604cc882ad1fb7d7f88044-goods.jpeg?imageView2/2/w/500/q/60/format/webp",
    "https://i.sstatic.net/CeCrU.jpg",
    "https://www.iboogaloo.com/wp-content/uploads/2011/05/Shirt-Red-Check-Ghosted-428x600.jpg",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8KQDkGtzB8g6P4sqxPUravoTYVFzOjyyOrg&s",
    "https://media.powerlook.in/catalog/product/d/p/dp11147521.jpg?aio=w-640"
]

# Predefined unique product data (15 base entries)
BASE_PRODUCT_ENTRIES = [
    {
        "name": "Arctic Explorer Parka",
        "description": "Designed to keep you warm in extreme conditions with sleek style.",
        "color": "Navy",
        "category": "Jackets",
        "gender": "Men",
        "tags": ["winter", "parka", "men", "outdoor"]
    },
    {
        "name": "Sierra Trail Hoodie",
        "description": "A rugged hoodie built for the outdoors and everyday adventures.",
        "color": "Olive",
        "category": "Hoodies",
        "gender": "Unisex",
        "tags": ["adventure", "hoodie", "unisex", "trail"]
    },
    {
        "name": "Crimson Classic Tee",
        "description": "Simple, soft, and perfect for layering or standing alone.",
        "color": "Crimson",
        "category": "Tops",
        "gender": "Women",
        "tags": ["basic", "tee", "women", "classic"]
    },
    {
        "name": "Sunset Boulevard Shirt",
        "description": "A breezy shirt with warm tones inspired by L.A. sunsets.",
        "color": "Orange",
        "category": "Shirts",
        "gender": "Men",
        "tags": ["sunset", "shirt", "men", "vacation"]
    },
    {
        "name": "Noir Minimalist Blazer",
        "description": "Clean lines and classic cut for the modern professional.",
        "color": "Black",
        "category": "Blazers",
        "gender": "Unisex",
        "tags": ["minimal", "blazer", "unisex", "workwear"]
    },
    {
        "name": "Ocean Spray Polo",
        "description": "Breathable comfort meets sleek coastal style.",
        "color": "Turquoise",
        "category": "Polos",
        "gender": "Men",
        "tags": ["polo", "casual", "beach", "men"]
    },
    {
        "name": "Lavender Lounge Tee",
        "description": "Ultra-soft fabric for relaxing days and calm vibes.",
        "color": "Lavender",
        "category": "Tops",
        "gender": "Women",
        "tags": ["lounge", "comfort", "tee", "women"]
    },
    {
        "name": "Denim Flex Shirt",
        "description": "A modern take on a classic denim shirt with extra stretch.",
        "color": "Denim Blue",
        "category": "Shirts",
        "gender": "Men",
        "tags": ["denim", "stretch", "shirt", "men"]
    },
    {
        "name": "Cactus Ridge Jacket",
        "description": "Inspired by desert explorers—rugged and ready.",
        "color": "Khaki",
        "category": "Jackets",
        "gender": "Unisex",
        "tags": ["desert", "jacket", "rugged", "unisex"]
    },
    {
        "name": "Blush Morning Blouse",
        "description": "Light and airy with subtle elegance for bright mornings.",
        "color": "Blush Pink",
        "category": "Shirts",
        "gender": "Women",
        "tags": ["elegant", "blouse", "morning", "women"]
    },
    {
        "name": "SteelCore Workout Tee",
        "description": "Engineered for performance with moisture-wicking technology.",
        "color": "Steel Grey",
        "category": "Tops",
        "gender": "Men",
        "tags": ["gym", "workout", "activewear", "men"]
    },
    {
        "name": "Rose Gold Bomber",
        "description": "Metallic edge meets soft feminine charm.",
        "color": "Rose Gold",
        "category": "Jackets",
        "gender": "Women",
        "tags": ["bomber", "metallic", "women", "fashion"]
    },
    {
        "name": "Citrus Pop Polo",
        "description": "Bold color with a breathable finish for summer vibes.",
        "color": "Citrus Yellow",
        "category": "Polos",
        "gender": "Unisex",
        "tags": ["summer", "polo", "bold", "unisex"]
    },
    {
        "name": "Graphite Commute Blazer",
        "description": "Tailored for movement, perfect for hybrid workers.",
        "color": "Graphite",
        "category": "Blazers",
        "gender": "Men",
        "tags": ["commute", "blazer", "hybrid", "men"]
    },
    {
        "name": "Mint Breeze Hoodie",
        "description": "Cool mint tones with cozy fleece interior.",
        "color": "Mint Green",
        "category": "Hoodies",
        "gender": "Women",
        "tags": ["mint", "hoodie", "cozy", "women"]
    }
]

# Generate 30 product entries by duplicating and modifying the base entries
PRODUCT_ENTRIES = []
for i in range(30):
    base_entry = BASE_PRODUCT_ENTRIES[i % len(BASE_PRODUCT_ENTRIES)]
    # Create a unique name by adding a number
    unique_name = f"{base_entry['name']} #{i+1}"
    
    product_entry = {
        **base_entry,
        "name": unique_name,
        "description": f"{base_entry['description']} (Edition {i+1})"
    }
    PRODUCT_ENTRIES.append(product_entry)

def add_30_unique_products():
    """Add 30 uniquely described products."""
    print("🚀 Adding 30 unique products...")

    if not check_database_connection():
        print("❌ Cannot connect to database.")
        return False

    db = SessionLocal()

    try:
        all_brands = db.query(Brand).all()
        if not all_brands:
            print("❌ No brands found! Run create_mock_data.py first.")
            return False

        print(f"🏢 Found {len(all_brands)} brands to assign products to")

        new_products = []
        for i, entry in enumerate(PRODUCT_ENTRIES):
            brand = all_brands[i % len(all_brands)]
            image_url = IMAGE_URLS[i % len(IMAGE_URLS)]

            product_data = {
                **entry,
                "image_url": image_url,
                "item_url": f"https://example.com/shop/{entry['name'].lower().replace(' ', '-').replace('#', '')}",
                "brand_id": brand.id,
                "product_metadata": {"material": "Cotton Blend", "fit": "Regular"},
                "vector_id_combined": generate_combined_vector(image_url, entry["description"]),
            }

            existing = db.query(Product).filter(Product.name == entry["name"]).first()
            if not existing:
                product = Product(**product_data)
                db.add(product)
                new_products.append(product)

        db.commit()
        print(f"✅ Created {len(new_products)} new products")
        print(f"📊 Total Brands: {db.query(Brand).count()}")
        print(f"👕 Total Products: {db.query(Product).count()}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    add_30_unique_products()
