#!/usr/bin/env python3
"""
Database Creation Script for Cropix Backend
Creates all tables from SQLAlchemy models
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from db import Base, engine
from community.models import Post, Comment, Like

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    db_url = os.getenv("DATABASE_URL", "postgresql://cc_user:shaka3232@localhost:5432/cropix")
    
    # Extract database name from URL
    if "postgresql" in db_url:
        # Parse the database URL to get connection without database name
        parts = db_url.split("/")
        db_name = parts[-1]
        base_url = "/".join(parts[:-1])
        
        print(f"🔍 Checking if database '{db_name}' exists...")
        
        # Connect to postgres database to create cropix database
        admin_engine = create_engine(f"{base_url}/postgres")
        
        try:
            with admin_engine.connect() as conn:
                # Check if database exists
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
                if not result.fetchone():
                    print(f"📦 Creating database '{db_name}'...")
                    conn.execute(text("COMMIT"))
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    print(f"✅ Database '{db_name}' created successfully!")
                else:
                    print(f"✅ Database '{db_name}' already exists!")
        except Exception as e:
            print(f"⚠️  Database creation check failed: {e}")
            print("   Make sure PostgreSQL is running and credentials are correct")

def create_tables():
    """Create all tables from SQLAlchemy models"""
    print("🏗️  Creating database tables...")
    
    try:
        # Import all models to ensure they're registered
        from community.models import Post, Comment, Like
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Created tables: {', '.join(tables)}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

def main():
    print("🚀 Cropix Database Setup")
    print("=" * 30)
    
    try:
        create_database()
        create_tables()
        print("\n✅ Database setup completed successfully!")
        print("\n🔧 Next step: Run 'python seed_data.py' to add dummy data")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Verify database credentials")

if __name__ == "__main__":
    main()