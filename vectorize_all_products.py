#!/usr/bin/env python3
"""
Script to vectorize all existing products in the database
"""
import sys
import os
import time
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Product
from app.services.vector_service import VectorService

def vectorize_products_batch(product_ids: List[str], batch_size: int = 10) -> Dict[str, Any]:
    """Vectorize a batch of products"""
    
    db = next(get_db())
    vector_service = VectorService(db)
    
    try:
        # Convert string IDs to UUIDs
        from uuid import UUID
        uuids = [UUID(pid) for pid in product_ids]
        
        # Generate vectors
        result = vector_service.generate_vectors_batch(uuids, batch_size)
        
        return result
        
    except Exception as e:
        print(f"❌ Error vectorizing batch: {e}")
        return {
            'success': False,
            'error': str(e),
            'total_products': len(product_ids),
            'successful': 0,
            'failed': len(product_ids)
        }
    finally:
        db.close()

def vectorize_all_products():
    """Vectorize all products in the database"""
    
    print("🚀 Starting vectorization of all products...")
    
    db = next(get_db())
    
    try:
        # Get all products
        products = db.query(Product).all()
        
        if not products:
            print("❌ No products found in database")
            return
        
        print(f"📊 Found {len(products)} products to vectorize")
        
        # Check which products already have complete vectors
        products_with_all_vectors = db.query(Product).filter(
            Product.image_vector.isnot(None),
            Product.text_vector.isnot(None),
            Product.combined_vector.isnot(None)
        ).count()
        
        print(f"📈 {products_with_all_vectors} products already have all vectors")
        
        # Get products that need vectorization (missing image or combined vectors)
        products_needing_vectors = db.query(Product).filter(
            or_(
                Product.image_vector.is_(None),
                Product.combined_vector.is_(None)
            )
        ).all()
        
        if not products_needing_vectors:
            print("✅ All products already have complete vectors!")
            return
        
        print(f"🔄 {len(products_needing_vectors)} products need vectorization")
        
        # Vectorize products that need vectors
        product_ids = [str(p.id) for p in products_needing_vectors]
        
        # Process in batches
        batch_size = 5  # Smaller batch size for stability
        total_batches = (len(product_ids) + batch_size - 1) // batch_size
        
        print(f"📦 Processing in {total_batches} batches of {batch_size}")
        
        successful = 0
        failed = 0
        
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} products)")
            
            start_time = time.time()
            result = vectorize_products_batch(batch, batch_size)
            end_time = time.time()
            
            if 'error' not in result:
                successful += result.get('successful', 0)
                failed += result.get('failed', 0)
                
                print(f"✅ Batch {batch_num} completed in {end_time - start_time:.2f}s")
                print(f"   Successful: {result.get('successful', 0)}, Failed: {result.get('failed', 0)}")
            else:
                failed += len(batch)
                print(f"❌ Batch {batch_num} failed: {result.get('error', 'Unknown error')}")
            
            # Small delay between batches
            if i + batch_size < len(product_ids):
                time.sleep(1)
        
        print(f"\n🎉 Vectorization completed!")
        print(f"📊 Results: {successful} successful, {failed} failed")
        if successful + failed > 0:
            print(f"📈 Success rate: {(successful / (successful + failed) * 100):.1f}%")
        
        # Show final status
        final_status = db.query(Product).filter(
            Product.image_vector.isnot(None),
            Product.text_vector.isnot(None),
            Product.combined_vector.isnot(None)
        ).count()
        
        print(f"📊 Total products with all vectors: {final_status}/{len(products)}")
        print(f"📈 Coverage: {(final_status / len(products) * 100):.1f}%")
        
    except Exception as e:
        print(f"❌ Error during vectorization: {e}")
    finally:
        db.close()

def vectorize_specific_products(product_ids: List[str]):
    """Vectorize specific products by ID"""
    
    print(f"🚀 Vectorizing {len(product_ids)} specific products...")
    
    result = vectorize_products_batch(product_ids, batch_size=len(product_ids))
    
    if result.get('success', False):
        print(f"✅ Vectorization completed!")
        print(f"📊 Results: {result.get('successful', 0)} successful, {result.get('failed', 0)} failed")
    else:
        print(f"❌ Vectorization failed: {result.get('error', 'Unknown error')}")

def show_vectorization_status():
    """Show current vectorization status"""
    
    db = next(get_db())
    
    try:
        vector_service = VectorService(db)
        status = vector_service.get_vectorization_status()
        
        print("📊 Vectorization Status:")
        print(f"   Total products: {status['total_products']}")
        print(f"   With image vectors: {status['with_image_vectors']} ({status['image_coverage']}%)")
        print(f"   With text vectors: {status['with_text_vectors']} ({status['text_coverage']}%)")
        print(f"   With combined vectors: {status['with_combined_vectors']} ({status['combined_coverage']}%)")
        print(f"   With all vectors: {status['with_all_vectors']} ({status['full_coverage']}%)")
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    from sqlalchemy import or_
    
    parser = argparse.ArgumentParser(description="Vectorize products in the database")
    parser.add_argument("--all", action="store_true", help="Vectorize all products")
    parser.add_argument("--products", nargs="+", help="Vectorize specific products by ID")
    parser.add_argument("--status", action="store_true", help="Show vectorization status")
    
    args = parser.parse_args()
    
    if args.status:
        show_vectorization_status()
    elif args.products:
        vectorize_specific_products(args.products)
    elif args.all:
        vectorize_all_products()
    else:
        print("Please specify --all, --products <id1> <id2> ..., or --status")
        print("Example: python vectorize_all_products.py --all")
        print("Example: python vectorize_all_products.py --products 123 456 789")
        print("Example: python vectorize_all_products.py --status") 