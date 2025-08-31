"""
Advanced Vectorization System for Product Similarity
Handles image and text embeddings for finding similar products
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import requests
import io
import torch
from transformers import AutoTokenizer, AutoModel
import open_clip
from sentence_transformers import SentenceTransformer
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductVectorizer:
    """Advanced vectorization system for product similarity"""
    
    def __init__(self):
        self.image_model = None
        self.image_processor = None
        self.text_model = None
        self.text_tokenizer = None
        self.sentence_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the ML models for vectorization"""
        try:
            # Try to use persistent models first
            try:
                from app.utils.model_manager import get_model_manager
                model_manager = get_model_manager()
                
                if model_manager.is_ready():
                    logger.info("🚀 Using persistent ML models from ModelManager")
                    self.image_model = model_manager.get_clip_model()
                    self.image_processor = model_manager.get_clip_preprocessor()
                    self.sentence_model = model_manager.get_sentence_model()
                    
                    if all([self.image_model, self.image_processor, self.sentence_model]):
                        logger.info("✅ All persistent models loaded successfully")
                        return
                    else:
                        logger.warning("⚠️ Some persistent models missing, falling back to direct loading")
                else:
                    logger.info("📥 Persistent models not ready, loading directly...")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to load persistent models: {e}, loading directly...")
            
            # Fallback to direct model loading
            logger.info("Loading CLIP model for image and text embeddings...")
            self.image_model, _, self.image_processor = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
            
            logger.info("Loading sentence transformer for text embeddings...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("Vectorization models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vectorization models: {e}")
            raise
    
    def download_image(self, image_url: str) -> Optional[Image.Image]:
        """Download and process image from URL"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return None
    
    def generate_image_vector(self, image_url: str) -> Optional[List[float]]:
        """Generate image embedding using CLIP"""
        try:
            image = self.download_image(image_url)
            if not image:
                return None
            
            # Process image with CLIP
            inputs = self.image_processor(images=image, return_tensors="pt", padding=True)
            
            with torch.no_grad():
                image_features = self.image_model.get_image_features(**inputs)
                image_vector = image_features.squeeze().cpu().numpy().tolist()
            
            # Convert to regular Python floats
            return [float(x) for x in image_vector]
        except Exception as e:
            logger.error(f"Failed to generate image vector: {e}")
            return None
    
    def generate_text_vector(self, text: str) -> Optional[List[float]]:
        """Generate text embedding using sentence transformer"""
        try:
            if not text or not text.strip():
                return None
            
            # Use sentence transformer for better text embeddings
            text_vector = self.sentence_model.encode(text, convert_to_tensor=False)
            
            # Convert to regular Python floats
            return [float(x) for x in text_vector.tolist()]
        except Exception as e:
            logger.error(f"Failed to generate text vector: {e}")
            return None
    
    def generate_product_text(self, product: Any) -> str:
        """Generate comprehensive text representation of a product"""
        text_parts = []
        
        # Basic product information
        if product.name:
            text_parts.append(product.name)
        
        if product.description:
            text_parts.append(product.description)
        
        if product.category:
            text_parts.append(f"category: {product.category}")
        
        if product.color:
            text_parts.append(f"color: {product.color}")
        
        if product.tags:
            text_parts.extend(product.tags)
        
        # Brand information
        if hasattr(product, 'brand') and product.brand and product.brand.name:
            text_parts.append(f"brand: {product.brand.name}")
        
        # Price information
        if product.price:
            text_parts.append(f"price: {product.price}")
        
        return " ".join(text_parts)
    
    def generate_product_vectors(self, product: Any) -> Dict[str, Any]:
        """Generate both image and text vectors for a product"""
        try:
            vectors = {
                'image_vector': None,
                'text_vector': None,
                'combined_vector': None,
                'text_representation': None,
                'metadata': {}
            }
            
            # Generate text representation
            text_representation = self.generate_product_text(product)
            vectors['text_representation'] = text_representation
            
            # Generate text vector
            if text_representation:
                text_vector = self.generate_text_vector(text_representation)
                vectors['text_vector'] = text_vector
            
            # Generate image vector
            if product.image:
                image_vector = self.generate_image_vector(product.image)
                vectors['image_vector'] = image_vector
            
            # Create combined vector (weighted combination)
            if vectors['image_vector'] and vectors['text_vector']:
                combined_vector = self._combine_vectors(
                    vectors['image_vector'], 
                    vectors['text_vector'],
                    image_weight=0.6,
                    text_weight=0.4
                )
                vectors['combined_vector'] = combined_vector
            elif vectors['image_vector']:
                vectors['combined_vector'] = vectors['image_vector']
            elif vectors['text_vector']:
                vectors['combined_vector'] = vectors['text_vector']
            
            # Add metadata
            vectors['metadata'] = {
                'generated_at': datetime.utcnow().isoformat(),
                'has_image_vector': bool(vectors['image_vector']),
                'has_text_vector': bool(vectors['text_vector']),
                'has_combined_vector': bool(vectors['combined_vector']),
                'image_vector_dim': len(vectors['image_vector']) if vectors['image_vector'] else 0,
                'text_vector_dim': len(vectors['text_vector']) if vectors['text_vector'] else 0,
                'combined_vector_dim': len(vectors['combined_vector']) if vectors['combined_vector'] else 0
            }
            
            return vectors
            
        except Exception as e:
            logger.error(f"Failed to generate product vectors: {e}")
            return {
                'image_vector': None,
                'text_vector': None,
                'combined_vector': None,
                'text_representation': None,
                'metadata': {'error': str(e)}
            }
    
    def _combine_vectors(self, image_vector: List[float], text_vector: List[float], 
                        image_weight: float = 0.6, text_weight: float = 0.4) -> List[float]:
        """Combine image and text vectors with weights"""
        try:
            # Convert to regular Python floats
            image_vector = [float(x) for x in image_vector]
            text_vector = [float(x) for x in text_vector]
            
            # Normalize vectors
            image_norm = np.linalg.norm(image_vector)
            text_norm = np.linalg.norm(text_vector)
            
            if image_norm > 0:
                image_vector = [x / image_norm for x in image_vector]
            if text_norm > 0:
                text_vector = [x / text_norm for x in text_vector]
            
            # Pad shorter vector to match longer one
            max_len = max(len(image_vector), len(text_vector))
            
            if len(image_vector) < max_len:
                image_vector.extend([0.0] * (max_len - len(image_vector)))
            if len(text_vector) < max_len:
                text_vector.extend([0.0] * (max_len - len(text_vector)))
            
            # Weighted combination
            combined = [
                float(image_weight * img_val + text_weight * txt_val)
                for img_val, txt_val in zip(image_vector, text_vector)
            ]
            
            return combined
            
        except Exception as e:
            logger.error(f"Failed to combine vectors: {e}")
            return [float(x) for x in image_vector]  # Fallback to image vector
    
    def calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            if not vector1 or not vector2:
                return 0.0
            
            # Convert to numpy arrays
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Handle different lengths by padding
            max_len = max(len(v1), len(v2))
            if len(v1) < max_len:
                v1 = np.pad(v1, (0, max_len - len(v1)), 'constant')
            if len(v2) < max_len:
                v2 = np.pad(v2, (0, max_len - len(v2)), 'constant')
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def find_similar_products(self, query_vectors: Dict[str, List[float]], 
                            product_vectors: List[Dict[str, Any]], 
                            limit: int = 10,
                            weights: Optional[Dict[str, float]] = None) -> List[Tuple[Any, float]]:
        """Find similar products using multiple vector types"""
        
        if not weights:
            weights = {
                'image_similarity': 0.6,
                'text_similarity': 0.4
            }
        
        logger.info(f"🔍 Starting similarity search with {len(product_vectors)} candidate products")
        logger.info(f"📊 Query vectors available: {list(query_vectors.keys())}")
        logger.info(f"⚖️ Weights: {weights}")
        
        scored_products = []
        
        for i, product_vec in enumerate(product_vectors):
            product = product_vec['product']
            total_score = 0.0
            score_count = 0
            individual_scores = {}
            
            # Image similarity
            if ('image_vector' in query_vectors and 
                product_vec.get('image_vector') and 
                weights.get('image_similarity', 0) > 0):
                
                img_sim = self.calculate_similarity(
                    query_vectors['image_vector'], 
                    product_vec['image_vector']
                )
                weighted_img_score = img_sim * weights['image_similarity']
                total_score += weighted_img_score
                score_count += 1
                individual_scores['image_similarity'] = {
                    'raw_score': img_sim,
                    'weighted_score': weighted_img_score,
                    'weight': weights['image_similarity']
                }
                
                logger.debug(f"📸 Product {product.name}: Image similarity = {img_sim:.4f} (weighted: {weighted_img_score:.4f})")
            
            # Text similarity
            if ('text_vector' in query_vectors and 
                product_vec.get('text_vector') and 
                weights.get('text_similarity', 0) > 0):
                
                txt_sim = self.calculate_similarity(
                    query_vectors['text_vector'], 
                    product_vec['text_vector']
                )
                weighted_txt_score = txt_sim * weights['text_similarity']
                total_score += weighted_txt_score
                score_count += 1
                individual_scores['text_similarity'] = {
                    'raw_score': txt_sim,
                    'weighted_score': weighted_txt_score,
                    'weight': weights['text_similarity']
                }
                
                logger.debug(f"📝 Product {product.name}: Text similarity = {txt_sim:.4f} (weighted: {weighted_txt_score:.4f})")
            
            # Combined vector similarity (fallback)
            if score_count == 0 and product_vec.get('combined_vector'):
                if 'combined_vector' in query_vectors:
                    combined_sim = self.calculate_similarity(
                        query_vectors['combined_vector'], 
                        product_vec['combined_vector']
                    )
                    total_score = combined_sim
                    score_count = 1
                    individual_scores['combined_similarity'] = {
                        'raw_score': combined_sim,
                        'weighted_score': combined_sim,
                        'weight': 1.0
                    }
                    
                    logger.debug(f"🔄 Product {product.name}: Combined similarity = {combined_sim:.4f}")
            
            # Normalize score
            if score_count > 0:
                final_score = total_score / score_count
                scored_products.append((product, final_score, individual_scores))
                
                logger.debug(f"🎯 Product {product.name}: Final score = {final_score:.4f} (from {score_count} vector types)")
            else:
                logger.debug(f"❌ Product {product.name}: No vector similarity calculated")
        
        # Sort by similarity score
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"🏆 Top 5 similarity scores:")
        for i, (product, score, scores) in enumerate(scored_products[:5]):
            logger.info(f"  {i+1}. {product.name}: {score:.4f}")
            for score_type, score_data in scores.items():
                logger.info(f"     - {score_type}: {score_data['raw_score']:.4f} (weighted: {score_data['weighted_score']:.4f})")
        
        # Return only the top results
        return [(product, score) for product, score, _ in scored_products[:limit]]

# Global vectorizer instance
_vectorizer = None

def get_vectorizer() -> ProductVectorizer:
    """Get or create the global vectorizer instance"""
    global _vectorizer
    if _vectorizer is None:
        _vectorizer = ProductVectorizer()
    return _vectorizer

def cosine_similarity(vector1: List[float], vector2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vectorizer = get_vectorizer()
    return vectorizer.calculate_similarity(vector1, vector2) 