from fastapi import FastAPI
from app.routers import users, swipes, recommendations, brands, products, wishlist, analytics, advanced_search
from app.db import check_database_connection

app = FastAPI(
    title="Fashion Platform API",
    description="A comprehensive API for a fashion/brand/product platform with users, swipes, wishlists, analytics, and advanced search",
    version="1.0.0"
)

# Check database connection on startup
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting Fashion Platform API...")
    if check_database_connection():
        print("🎉 API is ready to serve requests!")
    else:
        print("⚠️  API started but database connection failed. Please check your database configuration.")

# Include all routers
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(brands.router, prefix="/brands", tags=["brands"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(swipes.router, prefix="/swipes", tags=["swipes"])
app.include_router(wishlist.router, prefix="/wishlist", tags=["wishlist"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
app.include_router(advanced_search.router, prefix="/search", tags=["advanced-search"])

@app.get("/")
def root():
    return {"message": "Fashion Platform API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    db_status = check_database_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }
