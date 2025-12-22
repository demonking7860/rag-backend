"""Verify PostgreSQL setup is complete."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.db import connection

print("=" * 60)
print("PostgreSQL Setup Verification")
print("=" * 60)

# Check database engine
engine = settings.DATABASES['default']['ENGINE']
print(f"\n✅ Database Engine: {engine}")
if 'postgresql' in engine:
    print("   → Using PostgreSQL ✓")
else:
    print("   → ⚠️  NOT using PostgreSQL!")

# Check connection
with connection.cursor() as cursor:
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\n✅ PostgreSQL Version: {version.split(',')[0]}")
    
    # Check pgvector
    cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
    pgvector = cursor.fetchone()
    if pgvector:
        print(f"✅ pgvector Extension: {pgvector[1]}")
    else:
        print("⚠️  pgvector extension NOT installed!")
    
    # Check embedding column type
    cursor.execute("""
        SELECT column_name, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'rag_documentchunk' 
        AND column_name = 'embedding';
    """)
    embedding_col = cursor.fetchone()
    if embedding_col:
        col_type = embedding_col[1]
        print(f"\n✅ Embedding Column Type: {col_type}")
        if 'vector' in col_type.lower():
            print("   → Using VectorField (pgvector) ✓")
        else:
            print("   → ⚠️  Still using TextField!")
    
    # Check chunks
    cursor.execute("SELECT COUNT(*) FROM rag_documentchunk;")
    chunk_count = cursor.fetchone()[0]
    print(f"\n✅ Chunks in Database: {chunk_count}")

print("\n" + "=" * 60)
if 'postgresql' in engine and pgvector and 'vector' in (embedding_col[1] if embedding_col else ''):
    print("✅ PostgreSQL setup is COMPLETE and working!")
else:
    print("⚠️  Some issues detected. Check above.")
print("=" * 60)

