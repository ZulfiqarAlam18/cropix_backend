#!/usr/bin/env python3
"""
Database migration script to add users table for Cognito integration
"""

from sqlalchemy import create_engine, text
from community.models import Base, User, Post, Comment, Like
from db import get_db
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Create the users table and update existing relationships"""
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cropix")
    
    print("🚀 Starting database migration for Cognito integration...")
    print(f"📍 Database URL: {db_url}")
    
    # Create engine
    engine = create_engine(db_url)
    
    try:
        # Create all tables (will only create new ones)
        print("📊 Creating new tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your .env file with Cognito configuration:")
        print("   - COGNITO_USER_POOL_ID=your_pool_id")
        print("   - COGNITO_CLIENT_ID=your_client_id")
        print("   - COGNITO_REGION=your_region")
        print("2. Restart your server")
        print("3. Test the authentication endpoints")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()