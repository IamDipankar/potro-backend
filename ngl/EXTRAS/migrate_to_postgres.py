#!/usr/bin/env python3
"""
Database Migration Script
This script helps migrate from SQLite to PostgreSQL.
Run this after updating the database configuration.

Usage: "D:/Flask project/env/Scripts/python.exe" migrate_to_postgres.py
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base

async def create_tables():
    """Create all tables in the PostgreSQL database."""
    try:
        print("🔄 Creating database tables...")
        async with engine.begin() as conn:
            # Drop all tables (be careful in production!)
            # await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print(f"💡 Make sure the database exists and you have proper permissions")
        return False
    
    return True

async def test_connection():
    """Test the database connection."""
    try:
        print("🔄 Testing database connection...")
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()  # fetchone() is not async
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Common issues:")
        print("   - Check if the database host is accessible")
        print("   - Verify credentials in .env file")
        print("   - Ensure SSL is properly configured for remote databases")
        print("   - Check if your IP is whitelisted (if required)")
        return False

async def main():
    """Main migration function."""
    print("🔄 Starting PostgreSQL migration...")
    print("🌐 Connecting to remote Render PostgreSQL database...")
    
    # Test connection first
    if not await test_connection():
        print("❌ Migration failed - could not connect to database")
        return
    
    # Create tables
    if await create_tables():
        print("✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print('1. Install the new requirements: "D:/Flask project/env/Scripts/python.exe" -m pip install -r requirements.txt')
        print('2. Run your FastAPI application: "D:/Flask project/env/Scripts/python.exe" -m uvicorn main:app --reload')
    else:
        print("❌ Migration failed during table creation")

if __name__ == "__main__":
    asyncio.run(main())
