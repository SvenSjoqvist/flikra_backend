#!/usr/bin/env python3
"""
Script to create all database tables based on SQLAlchemy models.
Run this once to set up your database schema.
"""

from app.db import engine, Base, check_database_connection
from app.models import (
    User, Role, Brand, UserRole, Product, Swipe, 
    WishlistItem, Referral, BrandAnalyticsEvent, ReferralClick
)

def create_tables():
    """Create all tables in the database."""
    print("🚀 Creating database tables...")
    
    try:
        # Check database connection first
        if not check_database_connection():
            print("❌ Cannot connect to database. Please check your connection.")
            return False
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Insert default roles
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # Check if roles already exist
            existing_roles = db.query(Role).count()
            if existing_roles == 0:
                print("📝 Creating default roles...")
                default_roles = [
                    Role(name="user"),
                    Role(name="admin"), 
                    Role(name="brand_owner"),
                    Role(name="brand_team")
                ]
                
                for role in default_roles:
                    db.add(role)
                
                db.commit()
                print("✅ Default roles created!")
            else:
                print("ℹ️  Roles already exist, skipping role creation.")
                
        except Exception as e:
            print(f"⚠️  Error creating roles: {e}")
            db.rollback()
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("\n🎉 Database setup complete!")
        print("💡 You can now start your FastAPI server and use the API.")
    else:
        print("\n😞 Database setup failed. Please check the errors above.") 