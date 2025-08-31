"""
Model Manager for persisting ML models across requests
This eliminates the 7-8 second model loading time on each request
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
import torch
from sentence_transformers import SentenceTransformer
import open_clip

logger = logging.getLogger(__name__)

class ModelManager:
    """Singleton class to manage ML models across requests"""
    
    _instance = None
    _models_loaded = False
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._models_loaded:
            self._load_models()
    
    def _load_models(self):
        """Load all ML models once"""
        try:
            logger.info("🚀 Loading ML models for persistence...")
            
            # Load CLIP model
            logger.info("📸 Loading CLIP model...")
            self._models['clip'] = self._load_clip_model()
            
            # Load Sentence Transformer
            logger.info("📝 Loading Sentence Transformer...")
            self._models['sentence'] = self._load_sentence_model()
            
            # Load CLIP preprocessor
            logger.info("🔧 Loading CLIP preprocessor...")
            self._models['clip_preprocess'] = self._load_clip_preprocessor()
            
            self._models_loaded = True
            logger.info("✅ All ML models loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load ML models: {e}")
            raise
    
    def _load_clip_model(self):
        """Load CLIP model with device optimization"""
        try:
            # Use MPS (Apple Silicon) if available, otherwise CPU
            if torch.backends.mps.is_available():
                device = "mps"
                logger.info("🍎 Using MPS (Apple Silicon) for CLIP")
            elif torch.cuda.is_available():
                device = "cuda"
                logger.info("🚀 Using CUDA for CLIP")
            else:
                device = "cpu"
                logger.info("💻 Using CPU for CLIP")
            
            model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
            model = model.to(device)
            model.eval()  # Set to evaluation mode
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load CLIP model: {e}")
            raise
    
    def _load_sentence_model(self):
        """Load Sentence Transformer model"""
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Move to appropriate device
            if torch.backends.mps.is_available():
                model = model.to("mps")
                logger.info("🍎 Using MPS (Apple Silicon) for Sentence Transformer")
            elif torch.cuda.is_available():
                model = model.to("cuda")
                logger.info("🚀 Using CUDA for Sentence Transformer")
            else:
                logger.info("💻 Using CPU for Sentence Transformer")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load Sentence Transformer: {e}")
            raise
    
    def _load_clip_preprocessor(self):
        """Load CLIP preprocessor"""
        try:
            _, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
            return preprocess
        except Exception as e:
            logger.error(f"❌ Failed to load CLIP preprocessor: {e}")
            raise
    
    def get_clip_model(self):
        """Get CLIP model"""
        return self._models.get('clip')
    
    def get_sentence_model(self):
        """Get Sentence Transformer model"""
        return self._models.get('sentence')
    
    def get_clip_preprocessor(self):
        """Get CLIP preprocessor"""
        return self._models.get('clip_preprocess')
    
    def is_ready(self):
        """Check if models are loaded"""
        return self._models_loaded and all(self._models.values())
    
    def get_model_info(self):
        """Get information about loaded models"""
        if not self._models_loaded:
            return {"status": "not_loaded"}
        
        info = {
            "status": "loaded",
            "models": {},
            "device_info": {}
        }
        
        for name, model in self._models.items():
            if hasattr(model, 'device'):
                device = str(model.device)
            else:
                device = "unknown"
            
            info["models"][name] = {
                "loaded": model is not None,
                "device": device
            }
        
        return info

# Global instance
model_manager = ModelManager()

def get_model_manager():
    """Get the global model manager instance"""
    return model_manager 