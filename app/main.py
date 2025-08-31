# Load environment variables first
import os
from pathlib import Path

# Load .env file from project root
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    # Simple .env loading without external dependencies
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️ No .env file found at {env_path}")

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, products, brands, swipes, wishlist, brand_members, analytics, advanced_search, recommendations, reports
from app.routers.auth import router as auth_router
from app.utils.api_key_auth import require_api_key
from app.db import engine
from app.create_tables import create_tables
import logging
import sys
from sqlalchemy import text

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log')  # Also log to file
    ]
)

# Set specific loggers to INFO level
logging.getLogger('app.routers.recommendations').setLevel(logging.INFO)
logging.getLogger('app.services.recommendations').setLevel(logging.INFO)
logging.getLogger('app.services.vector_service').setLevel(logging.INFO)
logging.getLogger('app.utils.vectorization').setLevel(logging.INFO)

app = FastAPI(title="Cloth Brand API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Load ML models on server startup for persistence"""
    try:
        from app.utils.model_manager import get_model_manager
        model_manager = get_model_manager()
        
        if model_manager.is_ready():
            print("✅ ML models loaded and ready for fast vector recommendations!")
        else:
            print("⚠️ ML models not fully loaded")
            
    except Exception as e:
        print(f"❌ Failed to load ML models on startup: {e}")
        print("Vector recommendations will still work but may be slower")

# CORS middleware for NextJS frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # NextJS default ports
    allow_credentials=True,  # Important for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (no authentication required)
@app.get("/health")
def health_check():
    """Health check endpoint to verify API and database connectivity."""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Check ML model status
        try:
            from app.utils.model_manager import get_model_manager
            model_manager = get_model_manager()
            model_status = model_manager.get_model_info()
        except Exception as e:
            model_status = {"status": "error", "error": str(e)}
        
        return {
            "status": "healthy", 
            "database": "connected",
            "ml_models": model_status
        }
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# Include routers with API key authentication
app.include_router(
    users.router, 
    prefix="/users", 
    tags=["users"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    products.router, 
    prefix="/products", 
    tags=["products"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    brands.router, 
    prefix="/brands", 
    tags=["brands"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    swipes.router, 
    prefix="/swipes", 
    tags=["swipes"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    wishlist.router, 
    prefix="/wishlist", 
    tags=["wishlist"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    brand_members.router, 
    prefix="/brand-members", 
    tags=["brand-members"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    analytics.router, 
    prefix="/analytics", 
    tags=["analytics"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    advanced_search.router, 
    prefix="/search", 
    tags=["search"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    recommendations.router, 
    prefix="/recommendations", 
    tags=["recommendations"],
    dependencies=[Depends(require_api_key)]
)

app.include_router(
    reports.router, 
    prefix="/reports", 
    tags=["reports"],
    dependencies=[Depends(require_api_key)]
)

# Auth router (no API key required for login/logout)
app.include_router(
    auth_router, 
    prefix="/auth", 
    tags=["authentication"]
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("✅ Database tables created/verified")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
