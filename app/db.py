from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import logging

# Update with your PostgreSQL credentials - using local database
DATABASE_URL = "postgresql://postgres:Igloo100.@localhost:5432/clothbrand"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_connection():
    """Check if the database connection is working."""
    try:
        with engine.connect() as connection:
            # Test the connection with a simple query
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ Database connection successful!")
            return True
    except SQLAlchemyError as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Tip: Make sure PostgreSQL is running and check your database name, username, and password")
        return False
    except Exception as e:
        print(f"❌ Unexpected error connecting to database: {e}")
        return False

# Test connection when module is imported
if __name__ == "__main__":
    check_database_connection()
