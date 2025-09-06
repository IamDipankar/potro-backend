#!/usr/bin/env python3
"""
Simple connection test for PostgreSQL
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection_methods():
    """Test different connection methods"""
    
    # Method 1: Using DATABASE_URL from .env
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("🔄 Testing Method 1: Using DATABASE_URL from .env")
        print(f"URL (partial): {database_url[:50]}...")
        try:
            # Convert to asyncpg format and add SSL
            asyncpg_url = database_url.replace("postgresql://", "postgresql://") + "?ssl=require"
            conn = await asyncpg.connect(asyncpg_url)
            result = await conn.fetchval("SELECT 1")
            await conn.close()
            print("✅ Method 1: Connection successful!")
            return True
        except Exception as e:
            print(f"❌ Method 1 failed: {e}")
    
    # Method 2: Using individual parameters
    print("\n🔄 Testing Method 2: Using individual parameters")
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DATABASE_HOST"),
            port=int(os.getenv("DATABASE_PORT", "5432")),
            database=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            ssl="require"
        )
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        print("✅ Method 2: Connection successful!")
        return True
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Method 3: Try without SSL
    print("\n🔄 Testing Method 3: Without SSL requirement")
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DATABASE_HOST"),
            port=int(os.getenv("DATABASE_PORT", "5432")),
            database=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD")
        )
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        print("✅ Method 3: Connection successful!")
        return True
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    return False

async def main():
    print("🔍 PostgreSQL Connection Test")
    print("=============================")
    
    # Show loaded environment variables (masked)
    print(f"🔧 Loaded configuration:")
    print(f"   HOST: {os.getenv('DATABASE_HOST')}")
    print(f"   PORT: {os.getenv('DATABASE_PORT')}")
    print(f"   DATABASE: {os.getenv('DATABASE_NAME')}")
    print(f"   USER: {os.getenv('DATABASE_USER')}")
    print(f"   PASSWORD: {'*' * len(os.getenv('DATABASE_PASSWORD', ''))}")
    print(f"   URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}{'...' if os.getenv('DATABASE_URL') and len(os.getenv('DATABASE_URL')) > 50 else ''}")
    print()
    
    success = await test_connection_methods()
    
    if not success:
        print("\n❌ All connection methods failed!")
        print("\n💡 Possible solutions:")
        print("   1. Check if the database is fully provisioned in Render")
        print("   2. Verify the credentials haven't changed")
        print("   3. Ensure your IP is still whitelisted")
        print("   4. Try connecting from Render's dashboard first")
    else:
        print("\n✅ Connection successful! Database is ready for migration.")

if __name__ == "__main__":
    asyncio.run(main())
