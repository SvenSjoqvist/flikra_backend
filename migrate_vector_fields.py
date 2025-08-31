#!/usr/bin/env python3
"""
Migration script to add vector fields to the products table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.db import engine, Base
from app.models import Product

def add_vector_fields():
    """Add vector fields to the products table."""
    
    print("🔧 Adding vector fields to products table...")
    
    with engine.connect() as conn:
        # Check existing columns
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('products')]
        
        print(f"Existing columns: {existing_columns}")
        
        # Add image_vector column if it doesn't exist
        if 'image_vector' not in existing_columns:
            print("Adding image_vector column...")
            conn.execute(text("ALTER TABLE products ADD COLUMN image_vector FLOAT[]"))
        
        # Add text_vector column if it doesn't exist
        if 'text_vector' not in existing_columns:
            print("Adding text_vector column...")
            conn.execute(text("ALTER TABLE products ADD COLUMN text_vector FLOAT[]"))
        
        # Add combined_vector column if it doesn't exist
        if 'combined_vector' not in existing_columns:
            print("Adding combined_vector column...")
            conn.execute(text("ALTER TABLE products ADD COLUMN combined_vector FLOAT[]"))
        
        # Add vector_metadata column if it doesn't exist
        if 'vector_metadata' not in existing_columns:
            print("Adding vector_metadata column...")
            conn.execute(text("ALTER TABLE products ADD COLUMN vector_metadata TEXT"))
        
        # Commit changes
        conn.commit()
        
        print("✅ Vector fields added successfully!")
        
        # Verify the changes
        inspector = inspect(engine)
        updated_columns = [col['name'] for col in inspector.get_columns('products')]
        print(f"Updated columns: {updated_columns}")

if __name__ == "__main__":
    try:
        add_vector_fields()
    except Exception as e:
        print(f"❌ Error adding vector fields: {e}")
        sys.exit(1) 