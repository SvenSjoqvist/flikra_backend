from sqlalchemy import text
from app.db import engine, Base
import logging

logger = logging.getLogger(__name__)

def create_tables():
    """Create all database tables with optimized indexes for recommendations"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # OPTIMIZATION: Add performance indexes for recommendation queries
        with engine.connect() as conn:
            # Index for user swipes (most common query)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_swipes_user_action 
                ON swipes (user_id, action, created_at DESC)
            """))
            
            # Index for product category/brand filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_products_category_brand 
                ON products (category, brand_id)
            """))
            
            # Index for swipe joins
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_swipes_product_join 
                ON swipes (product_id, user_id, action)
            """))
            
            # Partial index for products with vectors (PostgreSQL syntax)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_products_with_vectors 
                ON products (id) WHERE combined_vector IS NOT NULL
            """))
            
            # Composite index for recommendation queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_recommendations_composite 
                ON products (category, brand_id) WHERE combined_vector IS NOT NULL
            """))
            
            conn.commit()
        
        logger.info("✅ Database tables and indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise

if __name__ == "__main__":
    create_tables() 