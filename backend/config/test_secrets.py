"""
Test script to verify AWS Secrets Manager integration.
Run this to test your RDS secret retrieval before starting Django.

Usage:
    python config/test_secrets.py
"""
import os
import sys
import django
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from config.aws_secrets import get_secret, get_database_url_from_secret

def test_secret_retrieval():
    """Test retrieving the secret from AWS Secrets Manager."""
    secret_name = getattr(settings, 'RDS_SECRET_NAME', None)
    secret_region = getattr(settings, 'RDS_SECRET_REGION', 'us-east-1')
    
    if not secret_name:
        print("❌ RDS_SECRET_NAME not set in settings")
        return False
    
    print(f"🔍 Testing secret retrieval: {secret_name}")
    print(f"📍 Region: {secret_region}")
    print()
    
    try:
        # Test 1: Retrieve raw secret
        print("Test 1: Retrieving secret from AWS Secrets Manager...")
        secret = get_secret(secret_name, secret_region)
        print("✅ Secret retrieved successfully!")
        print(f"   Keys found: {list(secret.keys())}")
        print(f"   Username: {secret.get('username', 'NOT FOUND')}")
        print(f"   Password: {'*' * len(secret.get('password', ''))} (hidden)")
        print()
        
        # Test 2: Build DATABASE_URL
        print("Test 2: Building DATABASE_URL...")
        db_host = getattr(settings, 'RDS_DB_HOST', None)
        db_name = getattr(settings, 'RDS_DB_NAME', 'postgres')
        
        if not db_host:
            print("⚠️  RDS_DB_HOST not set - checking if secret contains 'host'...")
            if 'host' in secret:
                print(f"   ✅ Found host in secret: {secret['host']}")
            else:
                print("   ❌ RDS_DB_HOST must be set in .env file")
                print("   Example: RDS_DB_HOST=database-1.xxxxx.us-east-1.rds.amazonaws.com")
                return False
        
        database_url = get_database_url_from_secret(
            secret_name,
            secret_region,
            db_host=db_host,
            db_name=db_name
        )
        
        # Mask password in URL for display
        import re
        masked_url = re.sub(r':([^:@]+)@', ':****@', database_url)
        print(f"✅ DATABASE_URL built successfully!")
        print(f"   {masked_url}")
        print()
        
        # Test 3: Test database connection
        print("Test 3: Testing database connection...")
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
            print(f"✅ Database connection successful!")
            print(f"   PostgreSQL version: {version}")
            print()
            
            # Test 4: Check pgvector extension
            print("Test 4: Checking pgvector extension...")
            with connection.cursor() as cursor:
                cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
                pgvector_exists = cursor.fetchone()[0]
            
            if pgvector_exists:
                print("✅ pgvector extension is installed")
            else:
                print("⚠️  pgvector extension not found")
                print("   Run: CREATE EXTENSION vector;")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            print("   Check your RDS_DB_HOST and RDS_DB_NAME settings")
            return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Check AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("2. Verify IAM permissions for Secrets Manager")
        print("3. Ensure RDS_SECRET_NAME is correct")
        print("4. Check RDS_DB_HOST and RDS_DB_NAME in .env")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("AWS Secrets Manager & RDS Connection Test")
    print("=" * 60)
    print()
    
    success = test_secret_retrieval()
    
    print("=" * 60)
    if success:
        print("✅ All tests passed! Your RDS configuration is working.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

