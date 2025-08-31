#!/usr/bin/env python3
"""
Script to build FAISS indexes for fast vector similarity search.
This will dramatically improve the performance of vector recommendations.
"""

import os
import sys
import pickle
import numpy as np
from pathlib import Path
import json

# Add the app directory to the path
sys.path.append('app')

from app.db import get_db
from app.models import Product
from app.services.vector_service import VectorService

def build_faiss_indexes():
    """Build FAISS indexes for all vector types"""
    print("🔨 Building FAISS indexes for fast vector search...")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize vector service
        vector_service = VectorService(db)
        
        # Check if FAISS is available
        try:
            import faiss
            print("✅ FAISS is available")
        except ImportError:
            print("❌ FAISS not available. Install with: pip install faiss-cpu")
            return False
        
        # Get all products with vectors
        products = db.query(Product).filter(
            Product.combined_vector.isnot(None)
        ).all()
        
        if not products:
            print("❌ No products with vectors found. Run vectorization first.")
            return False
        
        print(f"📦 Found {len(products)} products with vectors")
        
        # Create indexes directory
        indexes_dir = Path("vector_indexes")
        indexes_dir.mkdir(exist_ok=True)
        
        # Group products by vector dimension to handle inconsistencies
        print("🔍 Analyzing vector dimensions...")
        dimension_groups = {}
        
        for product in products:
            if product.combined_vector:
                dimension = len(product.combined_vector)
                if dimension not in dimension_groups:
                    dimension_groups[dimension] = []
                dimension_groups[dimension].append(product)
        
        print(f"📊 Found {len(dimension_groups)} different vector dimensions:")
        for dim, products_list in dimension_groups.items():
            print(f"   - {dim} dimensions: {len(products_list)} products")
        
        # Build separate indexes for each dimension group
        for dimension, products_list in dimension_groups.items():
            print(f"\n🚀 Building index for {dimension}-dimensional vectors ({len(products_list)} products)...")
            
            # Prepare vectors for this dimension
            vectors = []
            mapping = {}
            
            for i, product in enumerate(products_list):
                vector = np.array(product.combined_vector, dtype=np.float32)
                vectors.append(vector)
                mapping[i] = product.id
            
            if vectors:
                vectors = np.vstack(vectors)
                
                # Create FAISS index for this dimension
                index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
                
                # Normalize vectors for cosine similarity
                faiss.normalize_L2(vectors)
                
                # Add vectors to index
                index.add(vectors)
                
                # Save index and mapping with dimension suffix
                index_path = indexes_dir / f"combined_index_{dimension}d.faiss"
                mapping_path = indexes_dir / f"combined_mapping_{dimension}d.pkl"
                
                faiss.write_index(index, str(index_path))
                with open(mapping_path, 'wb') as f:
                    pickle.dump(mapping, f)
                
                print(f"✅ {dimension}D index built: {index.ntotal} vectors")
                print(f"   Saved to: {index_path}")
                print(f"   Mapping saved to: {mapping_path}")
        
        # Build image vector index if available
        print("\n🖼️ Building image vector index...")
        image_vectors = []
        image_mapping = {}
        
        for i, product in enumerate(products):
            if product.image_vector:
                vector = np.array(product.image_vector, dtype=np.float32)
                image_vectors.append(vector)
                image_mapping[i] = product.id
        
        if image_vectors:
            image_vectors = np.vstack(image_vectors)
            dimension = image_vectors.shape[1]
            
            index = faiss.IndexFlatIP(dimension)
            faiss.normalize_L2(image_vectors)
            index.add(image_vectors)
            
            index_path = indexes_dir / "image_index.faiss"
            mapping_path = indexes_dir / "image_mapping.pkl"
            
            faiss.write_index(index, str(index_path))
            with open(mapping_path, 'wb') as f:
                pickle.dump(image_mapping, f)
            
            print(f"✅ Image index built: {index.ntotal} vectors, {dimension} dimensions")
        
        # Build text vector index if available
        print("\n📝 Building text vector index...")
        text_vectors = []
        text_mapping = {}
        
        for i, product in enumerate(products):
            if product.text_vector:
                vector = np.array(product.text_vector, dtype=np.float32)
                text_vectors.append(vector)
                text_mapping[i] = product.id
        
        if text_vectors:
            text_vectors = np.vstack(text_vectors)
            dimension = text_vectors.shape[1]
            
            index = faiss.IndexFlatIP(dimension)
            faiss.normalize_L2(text_vectors)
            index.add(text_vectors)
            
            index_path = indexes_dir / "text_index.faiss"
            mapping_path = indexes_dir / "text_mapping.pkl"
            
            faiss.write_index(index, str(index_path))
            with open(mapping_path, 'wb') as f:
                pickle.dump(text_mapping, f)
            
            print(f"✅ Text index built: {index.ntotal} vectors, {dimension} dimensions")
        
        print("\n🎉 FAISS indexes built successfully!")
        print("📈 Vector recommendations should now be 10-100x faster!")
        
        # Create a dimension mapping file for the service to use
        dimension_info = {
            'dimensions': list(dimension_groups.keys()),
            'total_products': len(products),
            'dimension_counts': {dim: len(products_list) for dim, products_list in dimension_groups.items()}
        }
        
        dimension_path = indexes_dir / "dimension_info.json"
        with open(dimension_path, 'w') as f:
            json.dump(dimension_info, f, indent=2)
        
        print(f"📋 Dimension info saved to: {dimension_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to build FAISS indexes: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = build_faiss_indexes()
    if success:
        print("\n🚀 You can now restart your server for faster vector recommendations!")
    else:
        print("\n❌ Failed to build indexes. Check the error messages above.") 