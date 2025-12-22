"""
Install pgvector extension on PostgreSQL database.
Run: python manage.py shell < config/install_pgvector.py
Or: python -c "exec(open('config/install_pgvector.py').read())"
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        # Check if extension exists
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        exists = cursor.fetchone()
        
        if exists:
            print("✅ pgvector extension is already installed")
        else:
            # Install extension
            print("Installing pgvector extension...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            connection.commit()
            print("✅ pgvector extension installed successfully")
        
        # Verify installation
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        version = cursor.fetchone()
        if version:
            print(f"✅ pgvector version: {version[0]}")
        
        # Test vector operations
        cursor.execute("SELECT vector('[1,2,3]'::float[]);")
        result = cursor.fetchone()
        print(f"✅ Vector test successful: {result[0]}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)

