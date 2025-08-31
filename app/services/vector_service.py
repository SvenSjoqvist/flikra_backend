"""
Vector Service for managing product vectors and similarity search
"""
import logging
import json
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
import numpy as np
import pickle
import os
from pathlib import Path

from app.models import Product, Swipe
from app.utils.vectorization import get_vectorizer, ProductVectorizer

logger = logging.getLogger(__name__)

class VectorService:
    """Service for managing product vectors and similarity search"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vectorizer = ProductVectorizer()
        
        # FAISS indexes for fast similarity search
        self.faiss_indexes = {}
        self.vector_cache = {}
        
        # OPTIMIZATION: Add preference vector cache
        self.preference_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Initialize FAISS indexes
        self._initialize_faiss_indexes()
        
        logger.info("✅ VectorService initialized with FAISS and caching")
    
    def _initialize_faiss_indexes(self):
        """Initialize FAISS indexes for efficient similarity search"""
        try:
            import faiss
            
            # Create indexes directory
            indexes_dir = Path("vector_indexes")
            indexes_dir.mkdir(exist_ok=True)
            
            # Load dimension info if available
            dimension_info_path = indexes_dir / "dimension_info.json"
            if dimension_info_path.exists():
                import json
                with open(dimension_info_path, 'r') as f:
                    self.dimension_info = json.load(f)
                logger.info(f"📊 Loaded dimension info: {self.dimension_info}")
            else:
                self.dimension_info = None
            
            # Initialize indexes for different vector types
            self.indexes = {}
            
            # Load combined vector indexes for different dimensions
            if self.dimension_info:
                for dimension in self.dimension_info['dimensions']:
                    index_path = indexes_dir / f"combined_index_{dimension}d.faiss"
                    mapping_path = indexes_dir / f"combined_mapping_{dimension}d.pkl"
                    
                    if index_path.exists() and mapping_path.exists():
                        try:
                            index = faiss.read_index(str(index_path))
                            with open(mapping_path, 'rb') as f:
                                mapping = pickle.load(f)
                            
                            self.indexes[f'combined_{dimension}d'] = {
                                'index': index,
                                'mapping': mapping,
                                'dimension': dimension
                            }
                            logger.info(f"📂 Loaded {dimension}D combined index with {index.ntotal} vectors")
                        except Exception as e:
                            logger.error(f"Failed to load {dimension}D index: {e}")
            
            # Load image and text indexes
            for vector_type in ['image', 'text']:
                index_path = indexes_dir / f"{vector_type}_index.faiss"
                mapping_path = indexes_dir / f"{vector_type}_mapping.pkl"
                
                if index_path.exists() and mapping_path.exists():
                    try:
                        index = faiss.read_index(str(index_path))
                        with open(mapping_path, 'rb') as f:
                            mapping = pickle.load(f)
                        
                        self.indexes[vector_type] = {
                            'index': index,
                            'mapping': mapping
                        }
                        logger.info(f"📂 Loaded {vector_type} index with {index.ntotal} vectors")
                    except Exception as e:
                        logger.error(f"Failed to load {vector_type} index: {e}")
            
            logger.info(f"✅ FAISS indexes initialized: {list(self.indexes.keys())}")
            
        except ImportError:
            logger.warning("⚠️ FAISS not available, falling back to brute force search")
            self.indexes = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize FAISS indexes: {e}")
            self.indexes = None
    
    def _load_or_create_index(self, vector_type: str, dimension: int):
        """Load existing FAISS index or create new one"""
        try:
            import faiss
            
            index_path = f"vector_indexes/{vector_type}_index.faiss"
            mapping_path = f"vector_indexes/{vector_type}_mapping.pkl"
            
            if os.path.exists(index_path) and os.path.exists(mapping_path):
                # Load existing index
                index = faiss.read_index(index_path)
                with open(mapping_path, 'rb') as f:
                    mapping = pickle.load(f)
                logger.info(f"📂 Loaded existing {vector_type} index with {index.ntotal} vectors")
                return {'index': index, 'mapping': mapping}
            else:
                # Create new index
                index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
                mapping = {}
                logger.info(f"🆕 Created new {vector_type} index")
                return {'index': index, 'mapping': mapping}
                
        except Exception as e:
            logger.error(f"Failed to load/create {vector_type} index: {e}")
            return None
    
    def _load_product_mappings(self) -> Dict[str, Dict[int, UUID]]:
        """Load product ID mappings for all index types"""
        mappings = {}
        for vector_type in ['image', 'text', 'combined']:
            mapping_path = f"vector_indexes/{vector_type}_mapping.pkl"
            if os.path.exists(mapping_path):
                with open(mapping_path, 'rb') as f:
                    mappings[vector_type] = pickle.load(f)
        return mappings
    
    def _save_index(self, vector_type: str):
        """Save FAISS index and mapping to disk"""
        try:
            if vector_type in self.indexes and self.indexes[vector_type]:
                index_data = self.indexes[vector_type]
                index_path = f"vector_indexes/{vector_type}_index.faiss"
                mapping_path = f"vector_indexes/{vector_type}_mapping.pkl"
                
                import faiss
                faiss.write_index(index_data['index'], index_path)
                
                with open(mapping_path, 'wb') as f:
                    pickle.dump(index_data['mapping'], f)
                
                logger.info(f"💾 Saved {vector_type} index with {index_data['index'].ntotal} vectors")
                
        except Exception as e:
            logger.error(f"Failed to save {vector_type} index: {e}")
    
    def add_product_to_index(self, product_id: UUID, vectors: Dict[str, List[float]]):
        """Add product vectors to FAISS indexes"""
        try:
            if not self.indexes:
                return
            
            import faiss
            
            for vector_type, vector in vectors.items():
                if vector_type in self.indexes and vector and self.indexes[vector_type]:
                    index_data = self.indexes[vector_type]
                    index = index_data['index']
                    mapping = index_data['mapping']
                    
                    # Convert to numpy array
                    vector_array = np.array([vector], dtype=np.float32)
                    
                    # Add to index
                    index.add(vector_array)
                    
                    # Update mapping
                    mapping[index.ntotal - 1] = product_id
                    
                    logger.debug(f"➕ Added {vector_type} vector for product {product_id} to index")
            
        except Exception as e:
            logger.error(f"Failed to add product {product_id} to indexes: {e}")
    
    def remove_product_from_index(self, product_id: UUID):
        """Remove product from FAISS indexes (requires rebuilding)"""
        try:
            if not self.indexes:
                return
            
            # FAISS doesn't support efficient deletion, so we'll mark for rebuild
            # In production, you might want to use a different approach
            logger.warning(f"Product {product_id} marked for index rebuild (FAISS limitation)")
            
        except Exception as e:
            logger.error(f"Failed to remove product {product_id} from indexes: {e}")
    
    def search_similar_vectors_faiss(self, query_vectors: Dict[str, List[float]], 
                                   limit: int = 10,
                                   weights: Optional[Dict[str, float]] = None) -> List[Tuple[UUID, float]]:
        """Search for similar vectors using FAISS"""
        try:
            if not self.indexes:
                return self._fallback_search(query_vectors, limit, weights)
            
            import faiss
            
            if not weights:
                weights = {'image_similarity': 0.6, 'text_similarity': 0.4}
            
            # Collect results from all vector types
            all_results = {}
            
            for vector_type, query_vector in query_vectors.items():
                if vector_type in self.indexes and self.indexes[vector_type]:
                    index_data = self.indexes[vector_type]
                    index = index_data['index']
                    mapping = index_data['mapping']
                    
                    if index.ntotal == 0:
                        continue
                    
                    # Convert query vector
                    query_array = np.array([query_vector], dtype=np.float32)
                    
                    # Search
                    scores, indices = index.search(query_array, min(limit * 2, index.ntotal))
                    
                    # Process results
                    weight = weights.get(f'{vector_type}_similarity', 1.0)
                    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                        if idx != -1:  # Valid index
                            product_id = mapping.get(idx)
                            if product_id:
                                if product_id not in all_results:
                                    all_results[product_id] = {'scores': [], 'weights': []}
                                all_results[product_id]['scores'].append(float(score))
                                all_results[product_id]['weights'].append(weight)
            
            # Combine scores
            final_results = []
            for product_id, data in all_results.items():
                if data['scores']:
                    # Weighted average
                    weighted_score = sum(s * w for s, w in zip(data['scores'], data['weights']))
                    total_weight = sum(data['weights'])
                    final_score = weighted_score / total_weight if total_weight > 0 else 0
                    final_results.append((product_id, final_score))
            
            # Sort and return top results
            final_results.sort(key=lambda x: x[1], reverse=True)
            return final_results[:limit]
            
        except Exception as e:
            logger.error(f"FAISS search failed: {e}, falling back to brute force")
            return self._fallback_search(query_vectors, limit, weights)
    
    def _fallback_search(self, query_vectors: Dict[str, List[float]], 
                        limit: int = 10,
                        weights: Optional[Dict[str, float]] = None) -> List[Tuple[UUID, float]]:
        """Fallback to brute force search when FAISS is not available"""
        try:
            # Get all products with vectors
            products = self.db.query(Product).filter(
                Product.combined_vector.isnot(None)
            ).all()
            
            scored_products = []
            
            for product in products:
                total_score = 0.0
                score_count = 0
                
                # Calculate similarity for each vector type
                for vector_type, query_vector in query_vectors.items():
                    product_vector = getattr(product, f'{vector_type}_vector', None)
                    if product_vector:
                        weight = weights.get(f'{vector_type}_similarity', 1.0) if weights else 1.0
                        similarity = self.vectorizer.calculate_similarity(query_vector, product_vector)
                        total_score += similarity * weight
                        score_count += 1
                
                if score_count > 0:
                    final_score = total_score / score_count
                    scored_products.append((product.id, final_score))
            
            # Sort and return top results
            scored_products.sort(key=lambda x: x[1], reverse=True)
            return scored_products[:limit]
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []
    
    def generate_vectors_for_product(self, product_id: UUID, force_regenerate: bool = False) -> Dict[str, Any]:
        """Generate vectors for a specific product"""
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {
                    'success': False,
                    'error': 'Product not found',
                    'product_id': str(product_id)
                }
            
            # Check cache first
            cache_key = f"vectors:{product_id}"
            if not force_regenerate and cache_key in self.vector_cache:
                logger.info(f"📋 Cache hit for product {product_id}")
                return {
                    'success': True,
                    'message': 'Vectors loaded from cache',
                    'product_id': str(product_id),
                    'regenerated': False,
                    'from_cache': True
                }
            
            # Check if vectors already exist (unless force_regenerate)
            if not force_regenerate and self._has_vectors(product):
                # Cache the existing vectors
                vectors = {
                    'image_vector': product.image_vector,
                    'text_vector': product.text_vector,
                    'combined_vector': product.combined_vector
                }
                self.vector_cache[cache_key] = vectors
                
                return {
                    'success': True,
                    'message': 'Vectors already exist',
                    'product_id': str(product_id),
                    'regenerated': False
                }
            
            # Generate vectors
            vectors = self.vectorizer.generate_product_vectors(product)
            
            # Update product with vectors
            product.image_vector = vectors['image_vector']
            product.text_vector = vectors['text_vector']
            product.combined_vector = vectors['combined_vector']
            product.vector_metadata = json.dumps(vectors['metadata'])
            
            # Commit to database
            self.db.commit()
            
            # Cache the vectors
            self.vector_cache[cache_key] = {
                'image_vector': vectors['image_vector'],
                'text_vector': vectors['text_vector'],
                'combined_vector': vectors['combined_vector']
            }
            
            # Add to FAISS indexes
            self.add_product_to_index(product_id, {
                'image': vectors['image_vector'],
                'text': vectors['text_vector'],
                'combined': vectors['combined_vector']
            })
            
            logger.info(f"Successfully generated vectors for product {product_id}")
            
            return {
                'success': True,
                'message': 'Vectors generated successfully',
                'product_id': str(product_id),
                'regenerated': True,
                'vector_info': {
                    'has_image_vector': bool(vectors['image_vector']),
                    'has_text_vector': bool(vectors['text_vector']),
                    'has_combined_vector': bool(vectors['combined_vector']),
                    'image_vector_dim': len(vectors['image_vector']) if vectors['image_vector'] else 0,
                    'text_vector_dim': len(vectors['text_vector']) if vectors['text_vector'] else 0,
                    'combined_vector_dim': len(vectors['combined_vector']) if vectors['combined_vector'] else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate vectors for product {product_id}: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'product_id': str(product_id)
            }
    
    def generate_vectors_batch(self, product_ids: List[UUID], batch_size: int = 10) -> Dict[str, Any]:
        """Generate vectors for multiple products in batches"""
        try:
            import time
            
            results = {
                'total_products': len(product_ids),
                'successful': 0,
                'failed': 0,
                'results': []
            }
            
            for i in range(0, len(product_ids), batch_size):
                batch = product_ids[i:i + batch_size]
                
                for product_id in batch:
                    result = self.generate_vectors_for_product(product_id)
                    results['results'].append(result)
                    
                    if result['success']:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                
                # Small delay between batches to avoid overwhelming the system
                if i + batch_size < len(product_ids):
                    time.sleep(0.1)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to generate vectors in batch: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_products': len(product_ids),
                'successful': 0,
                'failed': len(product_ids)
            }
    
    def generate_vectors_for_missing(self) -> Dict[str, Any]:
        """Generate vectors for all products that don't have them"""
        try:
            # Find products without vectors
            products_without_vectors = self.db.query(Product).filter(
                or_(
                    Product.image_vector.is_(None),
                    Product.text_vector.is_(None),
                    Product.combined_vector.is_(None)
                )
            ).all()
            
            product_ids = [p.id for p in products_without_vectors]
            
            if not product_ids:
                return {
                    'success': True,
                    'message': 'All products already have vectors',
                    'total_products': 0,
                    'successful': 0,
                    'failed': 0
                }
            
            return self.generate_vectors_batch(product_ids)
            
        except Exception as e:
            logger.error(f"Failed to generate vectors for missing products: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_similar_products(self, product_id: UUID, limit: int = 10, 
                            exclude_swiped_by: Optional[UUID] = None,
                            category_filter: Optional[str] = None,
                            brand_filter: Optional[UUID] = None,
                            weights: Optional[Dict[str, float]] = None) -> List[Tuple[Product, float]]:
        """Find similar products using vector similarity"""
        try:
            # Get the query product
            query_product = self.db.query(Product).filter(Product.id == product_id).first()
            if not query_product:
                return []
            
            # Check if query product has vectors
            if not self._has_vectors(query_product):
                return []
            
            # Build query for candidate products
            query = self.db.query(Product).filter(
                Product.id != product_id,
                Product.combined_vector.isnot(None)  # Must have at least combined vector
            )
            
            # Apply filters
            if exclude_swiped_by:
                swiped_ids = set(r[0] for r in self.db.query(Swipe.product_id).filter(
                    Swipe.user_id == exclude_swiped_by
                ).all())
                query = query.filter(~Product.id.in_(swiped_ids))
            
            if category_filter:
                query = query.filter(Product.category == category_filter)
            
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            # Get candidate products
            candidate_products = query.all()
            
            if not candidate_products:
                return []
            
            # Prepare query vectors
            query_vectors = {}
            if query_product.image_vector:
                query_vectors['image_vector'] = query_product.image_vector
            if query_product.text_vector:
                query_vectors['text_vector'] = query_product.text_vector
            if query_product.combined_vector:
                query_vectors['combined_vector'] = query_product.combined_vector
            
            # Prepare product vectors for comparison
            product_vectors = []
            for product in candidate_products:
                product_vec = {'product': product}
                if product.image_vector:
                    product_vec['image_vector'] = product.image_vector
                if product.text_vector:
                    product_vec['text_vector'] = product.text_vector
                if product.combined_vector:
                    product_vec['combined_vector'] = product.combined_vector
                product_vectors.append(product_vec)
            
            # Find similar products
            similar_products = self.vectorizer.find_similar_products(
                query_vectors=query_vectors,
                product_vectors=product_vectors,
                limit=limit,
                weights=weights
            )
            
            return similar_products
            
        except Exception as e:
            logger.error(f"Failed to find similar products for {product_id}: {e}")
            return []
    
    def find_similar_by_text(self, text_query: str, limit: int = 10,
                           exclude_swiped_by: Optional[UUID] = None,
                           category_filter: Optional[str] = None,
                           brand_filter: Optional[UUID] = None) -> List[Tuple[Product, float]]:
        """Find similar products using text query"""
        try:
            # Generate text vector for query
            text_vector = self.vectorizer.generate_text_vector(text_query)
            if not text_vector:
                return []
            
            # Build query for candidate products
            query = self.db.query(Product).filter(
                Product.text_vector.isnot(None)
            )
            
            # Apply filters
            if exclude_swiped_by:
                swiped_ids = set(r[0] for r in self.db.query(Swipe.product_id).filter(
                    Swipe.user_id == exclude_swiped_by
                ).all())
                query = query.filter(~Product.id.in_(swiped_ids))
            
            if category_filter:
                query = query.filter(Product.category == category_filter)
            
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            # Get candidate products
            candidate_products = query.all()
            
            if not candidate_products:
                return []
            
            # Calculate similarities
            scored_products = []
            for product in candidate_products:
                similarity = self.vectorizer.calculate_similarity(
                    text_vector, product.text_vector
                )
                scored_products.append((product, similarity))
            
            # Sort by similarity
            scored_products.sort(key=lambda x: x[1], reverse=True)
            return scored_products[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar products by text: {e}")
            return []
    
    def get_user_preference_vectors(self, user_id: UUID, limit_likes: int = 10) -> Dict[str, List[float]]:
        """Get aggregated preference vectors from user's liked products"""
        try:
            logger.info(f"🔍 Creating preference vectors for user {user_id} (max {limit_likes} recent liked products)")
            
            # Get user's most recent liked products (ordered by swipe time)
            liked_swipes = self.db.query(Swipe).filter(
                Swipe.user_id == user_id,
                Swipe.action == "right"
            ).order_by(
                Swipe.created_at.desc()  # Most recent first
            ).limit(limit_likes).all()
            
            logger.info(f"📊 Found {len(liked_swipes)} recent liked swipes for user {user_id}")
            
            if not liked_swipes:
                logger.warning(f"⚠️ No liked products found for user {user_id}")
                return {}
            
            # Get products with vectors
            product_ids = [s.product_id for s in liked_swipes]
            products = self.db.query(Product).filter(
                Product.id.in_(product_ids),
                Product.combined_vector.isnot(None)
            ).all()
            
            logger.info(f"✅ Found {len(products)} recent liked products with vectors")
            
            if not products:
                logger.warning(f"⚠️ No recent liked products with vectors found for user {user_id}")
                return {}
            
            # Log the recent liked products with timestamps
            for i, swipe in enumerate(liked_swipes):
                product = next((p for p in products if p.id == swipe.product_id), None)
                if product:
                    logger.info(f"   {i+1}. {product.name} (swiped: {swipe.created_at.strftime('%Y-%m-%d %H:%M')})")
            
            # Aggregate vectors (simple average)
            image_vectors = [p.image_vector for p in products if p.image_vector]
            text_vectors = [p.text_vector for p in products if p.text_vector]
            combined_vectors = [p.combined_vector for p in products if p.combined_vector]
            
            logger.info(f"📈 Vector aggregation:")
            logger.info(f"   - Image vectors: {len(image_vectors)}/{len(products)}")
            logger.info(f"   - Text vectors: {len(text_vectors)}/{len(products)}")
            logger.info(f"   - Combined vectors: {len(combined_vectors)}/{len(products)}")
            
            preference_vectors = {}
            
            if image_vectors:
                avg_image_vector = self._average_vectors(image_vectors)
                preference_vectors['image_vector'] = avg_image_vector
                logger.info(f"✅ Created image preference vector: {len(avg_image_vector)} dimensions")
            
            if text_vectors:
                avg_text_vector = self._average_vectors(text_vectors)
                preference_vectors['text_vector'] = avg_text_vector
                logger.info(f"✅ Created text preference vector: {len(avg_text_vector)} dimensions")
            
            if combined_vectors:
                avg_combined_vector = self._average_vectors(combined_vectors)
                preference_vectors['combined_vector'] = avg_combined_vector
                logger.info(f"✅ Created combined preference vector: {len(avg_combined_vector)} dimensions")
            
            logger.info(f"🎯 Final preference vectors: {list(preference_vectors.keys())}")
            return preference_vectors
            
        except Exception as e:
            logger.error(f"❌ Failed to get user preference vectors: {e}")
            return {}
    
    def get_vectorization_status(self) -> Dict[str, Any]:
        """Get overall vectorization status"""
        try:
            total_products = self.db.query(Product).count()
            
            products_with_image_vectors = self.db.query(Product).filter(
                Product.image_vector.isnot(None)
            ).count()
            
            products_with_text_vectors = self.db.query(Product).filter(
                Product.text_vector.isnot(None)
            ).count()
            
            products_with_combined_vectors = self.db.query(Product).filter(
                Product.combined_vector.isnot(None)
            ).count()
            
            products_with_all_vectors = self.db.query(Product).filter(
                and_(
                    Product.image_vector.isnot(None),
                    Product.text_vector.isnot(None),
                    Product.combined_vector.isnot(None)
                )
            ).count()
            
            return {
                'total_products': total_products,
                'with_image_vectors': products_with_image_vectors,
                'with_text_vectors': products_with_text_vectors,
                'with_combined_vectors': products_with_combined_vectors,
                'with_all_vectors': products_with_all_vectors,
                'image_coverage': round((products_with_image_vectors / total_products) * 100, 2) if total_products > 0 else 0,
                'text_coverage': round((products_with_text_vectors / total_products) * 100, 2) if total_products > 0 else 0,
                'combined_coverage': round((products_with_combined_vectors / total_products) * 100, 2) if total_products > 0 else 0,
                'full_coverage': round((products_with_all_vectors / total_products) * 100, 2) if total_products > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get vectorization status: {e}")
            return {'error': str(e)}
    
    def _has_vectors(self, product: Product) -> bool:
        """Check if product has all necessary vectors"""
        return bool(product.image_vector and product.text_vector and product.combined_vector)
    
    def _average_vectors(self, vectors: List[List[float]]) -> List[float]:
        """Average multiple vectors"""
        if not vectors:
            return []
        
        # Pad vectors to same length
        max_len = max(len(v) for v in vectors)
        padded_vectors = []
        
        for vector in vectors:
            if len(vector) < max_len:
                vector = vector + [0.0] * (max_len - len(vector))
            padded_vectors.append(vector)
        
        # Calculate average
        avg_vector = []
        for i in range(max_len):
            avg_val = sum(v[i] for v in padded_vectors) / len(padded_vectors)
            avg_vector.append(avg_val)
        
        return avg_vector 

    def find_similar_products_optimized(self, product_id: UUID, limit: int = 10, 
                                      exclude_swiped_by: Optional[UUID] = None,
                                      category_filter: Optional[str] = None,
                                      brand_filter: Optional[UUID] = None,
                                      weights: Optional[Dict[str, float]] = None) -> List[Tuple[Product, float]]:
        """Optimized similar products search using FAISS"""
        try:
            # Get the query product
            query_product = self.db.query(Product).filter(Product.id == product_id).first()
            if not query_product:
                return []
            
            # Check if query product has vectors
            if not self._has_vectors(query_product):
                return []
            
            # Prepare query vectors
            query_vectors = {}
            if query_product.image_vector:
                query_vectors['image'] = query_product.image_vector
            if query_product.text_vector:
                query_vectors['text'] = query_product.text_vector
            if query_product.combined_vector:
                query_vectors['combined'] = query_product.combined_vector
            
            # Use FAISS for fast similarity search
            similar_product_ids = self.search_similar_vectors_faiss(
                query_vectors=query_vectors,
                limit=limit * 2,  # Get more to allow for filtering
                weights=weights
            )
            
            if not similar_product_ids:
                return []
            
            # Get products with filters
            product_ids = [pid for pid, _ in similar_product_ids]
            query = self.db.query(Product).filter(Product.id.in_(product_ids))
            
            # Apply filters
            if exclude_swiped_by:
                swiped_ids = set(r[0] for r in self.db.query(Swipe.product_id).filter(
                    Swipe.user_id == exclude_swiped_by
                ).all())
                query = query.filter(~Product.id.in_(swiped_ids))
            
            if category_filter:
                query = query.filter(Product.category == category_filter)
            
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            products = query.all()
            
            # Create score mapping
            score_map = {pid: score for pid, score in similar_product_ids}
            
            # Return products with scores
            results = [(product, score_map.get(product.id, 0.0)) for product in products]
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar products for {product_id}: {e}")
            return []

    def get_user_preference_vectors_cached(self, user_id: UUID) -> Dict[str, List[float]]:
        """Get user preference vectors with caching for better performance"""
        cache_key = f"pref_vectors_{user_id}"
        
        # Check cache first
        if cache_key in self.preference_cache:
            cached_data = self.preference_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                logger.info(f"⚡ Cache HIT for user {user_id} preference vectors")
                return cached_data['vectors']
            else:
                # Cache expired, remove it
                del self.preference_cache[cache_key]
        
        # Generate preference vectors
        logger.info(f"❄️ Cache MISS for user {user_id} preference vectors")
        preference_vectors = self.get_user_preference_vectors(user_id)
        
        if preference_vectors:
            # Cache the result
            self.preference_cache[cache_key] = {
                'vectors': preference_vectors,
                'timestamp': time.time()
            }
            logger.info(f"💾 Cached preference vectors for user {user_id}")
        
        return preference_vectors

    def clear_cache(self, pattern: Optional[str] = None):
        """Clear vector cache"""
        try:
            if pattern:
                # Clear specific pattern
                keys_to_remove = [k for k in self.vector_cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self.vector_cache[key]
                logger.info(f"🗑️ Cleared {len(keys_to_remove)} cache entries matching '{pattern}'")
            else:
                # Clear all cache
                self.vector_cache.clear()
                logger.info("🗑️ Cleared all vector cache")
                
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            return {
                'total_entries': len(self.vector_cache),
                'memory_usage_mb': sum(len(str(v)) for v in self.vector_cache.values()) / (1024 * 1024),
                'cache_hit_rate': 0.0,  # Would need to track hits/misses
                'indexes_available': bool(self.indexes),
                'faiss_vectors': sum(index_data['index'].ntotal for index_data in self.indexes.values()) if self.indexes else 0
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {} 

    def generate_vectors_batch_async(self, product_ids: List[UUID], batch_size: int = 10) -> Dict[str, Any]:
        """Generate vectors for multiple products asynchronously"""
        try:
            import asyncio
            import concurrent.futures
            
            results = {
                'total_products': len(product_ids),
                'successful': 0,
                'failed': 0,
                'results': [],
                'processing': True
            }
            
            # Process in batches asynchronously
            async def process_batch(batch):
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    loop = asyncio.get_event_loop()
                    tasks = []
                    
                    for product_id in batch:
                        task = loop.run_in_executor(
                            executor, 
                            self.generate_vectors_for_product, 
                            product_id
                        )
                        tasks.append(task)
                    
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for i, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            results['failed'] += 1
                            results['results'].append({
                                'product_id': str(batch[i]),
                                'success': False,
                                'error': str(result)
                            })
                        else:
                            if result['success']:
                                results['successful'] += 1
                            else:
                                results['failed'] += 1
                            results['results'].append(result)
            
            # Process all batches
            batches = [product_ids[i:i + batch_size] for i in range(0, len(product_ids), batch_size)]
            
            async def process_all_batches():
                for batch in batches:
                    await process_batch(batch)
                results['processing'] = False
            
            # Start background task
            asyncio.create_task(process_all_batches())
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to start async vector generation: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing': False
            }

    def queue_vector_generation(self, product_ids: List[UUID], priority: str = "normal") -> str:
        """Queue vector generation for background processing"""
        try:
            import uuid
            
            # Generate job ID
            job_id = str(uuid.uuid4())
            
            # In a real implementation, you'd use a proper job queue like Celery or RQ
            # For now, we'll simulate with a simple queue
            job_data = {
                'job_id': job_id,
                'product_ids': product_ids,
                'priority': priority,
                'status': 'queued',
                'created_at': datetime.utcnow().isoformat(),
                'total_products': len(product_ids)
            }
            
            # Store job data (in production, use Redis or database)
            if not hasattr(self, 'job_queue'):
                self.job_queue = {}
            
            self.job_queue[job_id] = job_data
            
            # Start background processing
            self._process_vector_generation_job(job_id)
            
            logger.info(f"🚀 Queued vector generation job {job_id} for {len(product_ids)} products")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to queue vector generation: {e}")
            return None
    
    def _process_vector_generation_job(self, job_id: str):
        """Process vector generation job in background"""
        try:
            import threading
            
            def process_job():
                try:
                    job_data = self.job_queue.get(job_id)
                    if not job_data:
                        return
                    
                    # Update status
                    job_data['status'] = 'processing'
                    job_data['started_at'] = datetime.utcnow().isoformat()
                    
                    # Process products
                    successful = 0
                    failed = 0
                    
                    for product_id in job_data['product_ids']:
                        try:
                            result = self.generate_vectors_for_product(product_id)
                            if result['success']:
                                successful += 1
                            else:
                                failed += 1
                        except Exception as e:
                            failed += 1
                            logger.error(f"Failed to generate vectors for {product_id}: {e}")
                    
                    # Update job status
                    job_data['status'] = 'completed'
                    job_data['completed_at'] = datetime.utcnow().isoformat()
                    job_data['successful'] = successful
                    job_data['failed'] = failed
                    
                    logger.info(f"✅ Completed vector generation job {job_id}: {successful} successful, {failed} failed")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process vector generation job {job_id}: {e}")
                    if job_id in self.job_queue:
                        self.job_queue[job_id]['status'] = 'failed'
                        self.job_queue[job_id]['error'] = str(e)
            
            # Start background thread
            thread = threading.Thread(target=process_job, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start background processing for job {job_id}: {e}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of vector generation job"""
        try:
            if not hasattr(self, 'job_queue') or job_id not in self.job_queue:
                return {
                    'job_id': job_id,
                    'status': 'not_found',
                    'error': 'Job not found'
                }
            
            job_data = self.job_queue[job_id]
            
            # Calculate progress
            total = job_data.get('total_products', 0)
            successful = job_data.get('successful', 0)
            failed = job_data.get('failed', 0)
            processed = successful + failed
            
            progress = (processed / total * 100) if total > 0 else 0
            
            return {
                'job_id': job_id,
                'status': job_data['status'],
                'progress': round(progress, 2),
                'total_products': total,
                'processed': processed,
                'successful': successful,
                'failed': failed,
                'created_at': job_data.get('created_at'),
                'started_at': job_data.get('started_at'),
                'completed_at': job_data.get('completed_at'),
                'error': job_data.get('error')
            }
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return {
                'job_id': job_id,
                'status': 'error',
                'error': str(e)
            } 

    def get_user_preference_vectors_weighted(self, user_id: UUID, limit_likes: int = 10, 
                                           time_decay_days: int = 30) -> Dict[str, List[float]]:
        """Get time-weighted preference vectors from user's liked products with caching"""
        try:
            # OPTIMIZATION: Check cache first
            cache_key = f"pref_vectors_{user_id}_{limit_likes}_{time_decay_days}"
            if cache_key in self.preference_cache:
                cache_time, vectors = self.preference_cache[cache_key]
                if (datetime.utcnow() - cache_time).seconds < self.cache_ttl:
                    logger.info(f"📦 Returning cached preference vectors for user {user_id}")
                    return vectors
                else:
                    # Remove expired cache
                    del self.preference_cache[cache_key]
            
            logger.info(f"🔍 Creating time-weighted preference vectors for user {user_id}")
            
            # OPTIMIZATION: Single query with JOIN to get products and swipes
            liked_swipes_with_products = self.db.query(
                Swipe, Product
            ).join(
                Product, Swipe.product_id == Product.id
            ).filter(
                Swipe.user_id == user_id,
                Swipe.action == "right",
                Product.combined_vector.isnot(None)
            ).order_by(
                Swipe.created_at.desc()
            ).limit(limit_likes).all()
            
            logger.info(f"📊 Found {len(liked_swipes_with_products)} recent liked products with vectors")
            
            if not liked_swipes_with_products:
                logger.warning(f"⚠️ No liked products with vectors found for user {user_id}")
                return {}
            
            # Calculate time weights (more recent = higher weight)
            from datetime import datetime
            now = datetime.utcnow()
            
            product_weights = {}
            for swipe, product in liked_swipes_with_products:
                days_ago = (now - swipe.created_at).days
                # Exponential decay: weight = e^(-days/time_decay_days)
                weight = np.exp(-days_ago / time_decay_days)
                product_weights[product.id] = weight
                
                logger.info(f"   {product.name}: {weight:.3f} weight ({days_ago} days ago)")
            
            # OPTIMIZATION: Pre-allocate vectors for better performance
            products = [p for _, p in liked_swipes_with_products]
            
            # Weighted vector aggregation
            preference_vectors = {}
            
            # Image vectors
            image_vectors = []
            image_weights = []
            for product in products:
                if product.image_vector and product.id in product_weights:
                    image_vectors.append(product.image_vector)
                    image_weights.append(product_weights[product.id])
            
            if image_vectors:
                weighted_avg_image = self._weighted_average_vectors(image_vectors, image_weights)
                preference_vectors['image_vector'] = weighted_avg_image
                logger.info(f"✅ Created weighted image preference vector: {len(weighted_avg_image)} dimensions")
            
            # Text vectors
            text_vectors = []
            text_weights = []
            for product in products:
                if product.text_vector and product.id in product_weights:
                    text_vectors.append(product.text_vector)
                    text_weights.append(product_weights[product.id])
            
            if text_vectors:
                weighted_avg_text = self._weighted_average_vectors(text_vectors, text_weights)
                preference_vectors['text_vector'] = weighted_avg_text
                logger.info(f"✅ Created weighted text preference vector: {len(weighted_avg_text)} dimensions")
            
            # Combined vectors
            combined_vectors = []
            combined_weights = []
            for product in products:
                if product.combined_vector and product.id in product_weights:
                    combined_vectors.append(product.combined_vector)
                    combined_weights.append(product_weights[product.id])
            
            if combined_vectors:
                weighted_avg_combined = self._weighted_average_vectors(combined_vectors, combined_weights)
                preference_vectors['combined_vector'] = weighted_avg_combined
                logger.info(f"✅ Created weighted combined preference vector: {len(weighted_avg_combined)} dimensions")
            
            # OPTIMIZATION: Cache the result
            self.preference_cache[cache_key] = (datetime.utcnow(), preference_vectors)
            
            logger.info(f"🎯 Final weighted preference vectors: {list(preference_vectors.keys())}")
            return preference_vectors
            
        except Exception as e:
            logger.error(f"❌ Failed to get weighted user preference vectors: {e}")
            return {}
    
    def _weighted_average_vectors(self, vectors: List[List[float]], weights: List[float]) -> List[float]:
        """Calculate weighted average of vectors"""
        try:
            if not vectors or not weights or len(vectors) != len(weights):
                return self._average_vectors(vectors)
            
            # Normalize weights
            total_weight = sum(weights)
            if total_weight == 0:
                return self._average_vectors(vectors)
            
            normalized_weights = [w / total_weight for w in weights]
            
            # Calculate weighted average
            result = []
            for i in range(len(vectors[0])):
                weighted_sum = sum(vectors[j][i] * normalized_weights[j] for j in range(len(vectors)))
                result.append(weighted_sum)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate weighted average: {e}")
            return self._average_vectors(vectors) 

    def get_user_preference_vectors_balanced(self, user_id: UUID, limit_likes: int = 10, 
                                           limit_dislikes: int = 5, time_decay_days: int = 30) -> Dict[str, List[float]]:
        """Get balanced preference vectors considering both likes and dislikes"""
        try:
            logger.info(f"🔍 Creating balanced preference vectors for user {user_id}")
            
            # Get user's recent liked and disliked products
            liked_swipes = self.db.query(Swipe).filter(
                Swipe.user_id == user_id,
                Swipe.action == "right"
            ).order_by(Swipe.created_at.desc()).limit(limit_likes).all()
            
            disliked_swipes = self.db.query(Swipe).filter(
                Swipe.user_id == user_id,
                Swipe.action == "left"
            ).order_by(Swipe.created_at.desc()).limit(limit_dislikes).all()
            
            logger.info(f"📊 Found {len(liked_swipes)} recent likes and {len(disliked_swipes)} recent dislikes")
            
            if not liked_swipes and not disliked_swipes:
                logger.warning(f"⚠️ No swipe history found for user {user_id}")
                return {}
            
            # Get products with vectors
            all_product_ids = [s.product_id for s in liked_swipes + disliked_swipes]
            products = self.db.query(Product).filter(
                Product.id.in_(all_product_ids),
                Product.combined_vector.isnot(None)
            ).all()
            
            if not products:
                logger.warning(f"⚠️ No products with vectors found for user {user_id}")
                return {}
            
            # Calculate time weights
            from datetime import datetime
            now = datetime.utcnow()
            
            product_weights = {}
            for swipe in liked_swipes + disliked_swipes:
                days_ago = (now - swipe.created_at).days
                weight = np.exp(-days_ago / time_decay_days)
                # Negative weight for dislikes
                if swipe.action == "left":
                    weight = -weight * 0.5  # Dislikes have less impact but still matter
                product_weights[swipe.product_id] = weight
                
                product = next((p for p in products if p.id == swipe.product_id), None)
                if product:
                    action_symbol = "❤️" if swipe.action == "right" else "💔"
                    logger.info(f"   {action_symbol} {product.name}: {weight:.3f} weight ({days_ago} days ago)")
            
            # Create balanced preference vectors
            preference_vectors = {}
            
            # Image vectors
            image_vectors = []
            image_weights = []
            for product in products:
                if product.image_vector and product.id in product_weights:
                    image_vectors.append(product.image_vector)
                    image_weights.append(product_weights[product.id])
            
            if image_vectors:
                balanced_image = self._weighted_average_vectors(image_vectors, image_weights)
                preference_vectors['image_vector'] = balanced_image
                logger.info(f"✅ Created balanced image preference vector: {len(balanced_image)} dimensions")
            
            # Text vectors
            text_vectors = []
            text_weights = []
            for product in products:
                if product.text_vector and product.id in product_weights:
                    text_vectors.append(product.text_vector)
                    text_weights.append(product_weights[product.id])
            
            if text_vectors:
                balanced_text = self._weighted_average_vectors(text_vectors, text_weights)
                preference_vectors['text_vector'] = balanced_text
                logger.info(f"✅ Created balanced text preference vector: {len(balanced_text)} dimensions")
            
            # Combined vectors
            combined_vectors = []
            combined_weights = []
            for product in products:
                if product.combined_vector and product.id in product_weights:
                    combined_vectors.append(product.combined_vector)
                    combined_weights.append(product_weights[product.id])
            
            if combined_vectors:
                balanced_combined = self._weighted_average_vectors(combined_vectors, combined_weights)
                preference_vectors['combined_vector'] = balanced_combined
                logger.info(f"✅ Created balanced combined preference vector: {len(balanced_combined)} dimensions")
            
            logger.info(f"🎯 Final balanced preference vectors: {list(preference_vectors.keys())}")
            return preference_vectors
            
        except Exception as e:
            logger.error(f"❌ Failed to get balanced user preference vectors: {e}")
            return {} 

    def find_similar_products_faiss(self, query_vectors: Dict[str, List[float]], 
                                   limit: int = 10, exclude_ids: Optional[set] = None,
                                   category_filter: Optional[str] = None,
                                   brand_filter: Optional[UUID] = None) -> List[Tuple[Product, float]]:
        """Find similar products using FAISS indexes for fast similarity search"""
        try:
            if not self.indexes:
                logger.warning("⚠️ FAISS indexes not available, falling back to brute force")
                return []
            
            # Use combined vector for fastest search
            if 'combined_vector' not in query_vectors:
                logger.warning("⚠️ No combined vector available for FAISS search")
                return []
            
            query_vector = np.array(query_vectors['combined_vector'], dtype=np.float32)
            query_dimension = query_vector.shape[0]
            
            # Find the right index for this dimension
            index_key = None
            for key, index_data in self.indexes.items():
                if key.startswith('combined_') and index_data.get('dimension') == query_dimension:
                    index_key = key
                    break
            
            if not index_key:
                logger.warning(f"⚠️ No FAISS index available for {query_dimension}D vectors")
                return []
            
            # Get FAISS index
            combined_index = self.indexes[index_key]
            faiss_index = combined_index['index']
            product_mapping = combined_index['mapping']
            
            logger.info(f"🚀 Using {index_key} index for {query_dimension}D vectors")
            
            # Reshape query vector for FAISS
            query_vector = query_vector.reshape(1, -1)
            
            # Search FAISS index - expand search for more diversity
            search_limit = min(limit * 10, faiss_index.ntotal)  # Increased from 3x to 10x
            scores, indices = faiss_index.search(query_vector, search_limit)
            
            logger.info(f"🔍 FAISS search returned {len(indices[0])} indices, scores range: {scores[0].min():.4f} to {scores[0].max():.4f}")
            
            # Get products from database
            product_ids = []
            excluded_count = 0
            for idx in indices[0]:
                if idx in product_mapping:
                    product_id = product_mapping[idx]
                    if exclude_ids and product_id in exclude_ids:
                        excluded_count += 1
                        continue
                    product_ids.append(product_id)
                    if len(product_ids) >= limit * 5:  # Increased from 2x to 5x for more diversity
                        break
            
            logger.info(f"📊 Found {len(product_ids)} candidate products after excluding {excluded_count} swiped products")
            
            if not product_ids:
                logger.warning(f"⚠️ No products available after filtering. User may have swiped all products or FAISS search failed")
                return []
            
            # Query products with filters
            query = self.db.query(Product).filter(
                Product.id.in_(product_ids),
                Product.combined_vector.isnot(None)
            )
            
            if category_filter:
                query = query.filter(Product.category == category_filter)
            if brand_filter:
                query = query.filter(Product.brand_id == brand_filter)
            
            products = query.all()
            
            # Calculate final similarity scores and sort
            scored_products = []
            for product in products:
                if product.combined_vector:
                    similarity = self.calculate_similarity(
                        query_vectors['combined_vector'], 
                        product.combined_vector
                    )
                    scored_products.append((product, similarity))
                    logger.debug(f"🔍 Product {product.name}: similarity = {similarity:.4f}")
            
            # Sort by similarity score
            scored_products.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"🚀 FAISS search found {len(scored_products)} products")
            if scored_products:
                logger.info(f"🏆 Top similarity scores: {[f'{p.name}:{s:.4f}' for p, s in scored_products[:3]]}")
            return scored_products[:limit]
            
        except Exception as e:
            logger.error(f"❌ FAISS similarity search failed: {e}")
            return []
    
    def calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            
            v1 = np.array(vector1, dtype=np.float32)
            v2 = np.array(vector2, dtype=np.float32)
            
            # Check for zero vectors
            v1_norm_val = np.linalg.norm(v1)
            v2_norm_val = np.linalg.norm(v2)
            
            if v1_norm_val == 0 or v2_norm_val == 0:
                logger.warning(f"⚠️ Zero vector detected: v1_norm={v1_norm_val}, v2_norm={v2_norm_val}")
                return 0.0
            
            # Normalize vectors
            v1_norm = v1 / v1_norm_val
            v2_norm = v2 / v2_norm_val
            
            # Calculate cosine similarity
            similarity = np.dot(v1_norm, v2_norm)
            
            # Ensure similarity is in valid range
            similarity = max(-1.0, min(1.0, similarity))
            
            logger.debug(f"🔍 Similarity calculation: v1_norm={v1_norm_val:.4f}, v2_norm={v2_norm_val:.4f}, similarity={similarity:.4f}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"❌ Similarity calculation failed: {e}")
            import traceback
            traceback.print_exc()
            return 0.0 