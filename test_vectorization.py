#!/usr/bin/env python3
"""
Test script to debug vectorization
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.models import Product
from app.services.vector_service import VectorService

def test_vectorization():
    """Test vectorization with a few products"""
    
    db = next(get_db())
    vs = VectorService(db)
    
    try:
        # Get products with images
        products = db.query(Product).filter(Product.image.isnot(None)).limit(3).all()
        print(f'Testing {len(products)} products...')
        
        for i, product in enumerate(products):
            print(f'Processing {i+1}/{len(products)}: {product.name}')
            print(f'  Image: {product.image}')
            
            try:
                result = vs.generate_vectors_for_product(product.id, force_regenerate=True)
                print(f'  Success: {result["success"]}')
                if result["success"]:
                    print(f'  Vector info: {result.get("vector_info", {})}')
                else:
                    print(f'  Error: {result.get("error", "Unknown error")}')
            except Exception as e:
                print(f'  Exception: {e}')
            
            print()
    
    except Exception as e:
        print(f'Error: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    test_vectorization() 