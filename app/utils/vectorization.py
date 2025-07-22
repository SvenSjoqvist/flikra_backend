import torch
from transformers import CLIPProcessor, CLIPModel
import requests
from PIL import Image
from io import BytesIO
import numpy as np

# Load CLIP model and processor
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def download_image(image_url: str) -> Image.Image:
    """Download an image from a URL and return it as a PIL Image."""
    response = requests.get(image_url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))


def generate_combined_vector(image_url: str, description: str) -> list:
    """Generate a combined vector for a product using its image and description."""
    # Download image
    image = download_image(image_url)
    
    # Prepare inputs
    inputs = clip_processor(text=[description], images=[image], return_tensors="pt", padding=True)
    
    # Generate vector
    with torch.no_grad():
        outputs = clip_model(**inputs)
        image_features = outputs.image_embeds
        text_features = outputs.text_embeds
        
    # Combine vectors (e.g., by averaging)
    combined_vector = (image_features + text_features) / 2
    
    # Convert to list
    return combined_vector.squeeze().tolist() 


def cosine_similarity(vec1: list, vec2: list) -> float:
    """Calculate the cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2) 