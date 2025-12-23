#!/bin/bash
set -e

echo "Starting Django application..."

# Check and create pgvector extension if needed
echo "Checking pgvector extension..."
python << EOF
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
        exists = cursor.fetchone()[0]
        
        if not exists:
            print("WARNING: pgvector extension not found!")
            print("Attempting to create pgvector extension...")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                connection.commit()
                print("✓ pgvector extension created successfully")
            except Exception as e:
                print(f"ERROR: Could not create pgvector extension: {e}")
                print("Please ensure pgvector is installed in your PostgreSQL database.")
                sys.exit(1)
        else:
            print("✓ pgvector extension found")
except Exception as e:
    print(f"WARNING: Could not check pgvector: {e}")
    print("Continuing anyway - ensure pgvector is enabled in your database")
EOF

if [ $? -ne 0 ]; then
    echo "CRITICAL: pgvector extension setup failed"
    exit 1
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

