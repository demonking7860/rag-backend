import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.db import connection

print('=' * 50)
print('PostgreSQL Configuration Verification')
print('=' * 50)
print(f"Database Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Database Name: {settings.DATABASES['default'].get('NAME')}")
print(f"Host: {settings.DATABASES['default'].get('HOST')}")
print(f"Port: {settings.DATABASES['default'].get('PORT')}")
print(f"User: {settings.DATABASES['default'].get('USER')}")

with connection.cursor() as cur:
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"\nPostgreSQL Version: {version[:80]}...")
    
    # Check pgvector
    cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
    pgvector = cur.fetchone()
    if pgvector:
        print(f"\n✅ pgvector extension installed: version {pgvector[1]}")
    else:
        print("\n⚠️  pgvector extension NOT installed")
        print("   Run: CREATE EXTENSION vector;")
    
    # Check tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    print(f"\n✅ Database tables ({len(tables)}): {', '.join(tables)}")

print('=' * 50)

