#!/usr/bin/env python3
"""
Debug script to test database connection parameters
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Debug: Environment Variables")
print(f"DATABASE_HOST: {os.getenv('DATABASE_HOST')}")
print(f"DATABASE_PORT: {os.getenv('DATABASE_PORT')}")
print(f"DATABASE_NAME: {os.getenv('DATABASE_NAME')}")
print(f"DATABASE_USER: {os.getenv('DATABASE_USER')}")
print(f"DATABASE_PASSWORD: {'*' * len(os.getenv('DATABASE_PASSWORD', '')) if os.getenv('DATABASE_PASSWORD') else 'NOT SET'}")

print("\n🔍 Constructed DATABASE_URL:")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

# Hide password in URL for security
url_display = f"postgresql+asyncpg://{DATABASE_USER}:{'*' * len(DATABASE_PASSWORD) if DATABASE_PASSWORD else 'NOT_SET'}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?ssl=require"
print(url_display)

print("\n🔍 Checking .env file exists:")
env_path = ".env"
if os.path.exists(env_path):
    print(f"✅ .env file found at: {os.path.abspath(env_path)}")
    with open(env_path, 'r') as f:
        content = f.read()
        print(f"📄 .env content preview (first 200 chars):")
        print(content[:200] + "..." if len(content) > 200 else content)
else:
    print("❌ .env file not found")
