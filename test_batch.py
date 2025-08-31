#!/usr/bin/env python3
"""
Test script to debug batch vectorization
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.models import Product
from app.services.vector_service import VectorService

def test_batch_vectorization():
    """Test batch vectorization with a few products"""
    
    db = next(get_db())
    vs = VectorService(db)
    
    try:
        # Get products with images
        products = db.query(Product).filter(Product.image.isnot(None)).limit(5).all()
        product_ids = [p.id for p in products]
        
        print(f'Testing batch vectorization with {len(product_ids)} products...')
        
        result = vs.generate_vectors_batch(product_ids, batch_size=2)
        
        print(f'Batch result: {result}')
        
        if result.get('success', True):
            print(f'Successful: {result.get("successful", 0)}')
            print(f'Failed: {result.get("failed", 0)}')
            
            # Show individual results
            for i, res in enumerate(result.get('results', [])):
                print(f'  Product {i+1}: {"Success" if res.get("success") else "Failed"}')
                if not res.get("success"):
                    print(f'    Error: {res.get("error", "Unknown")}')
        else:
            print(f'Batch failed: {result.get("error", "Unknown error")}')
    
    except Exception as e:
        print(f'Error: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    test_batch_vectorization() 