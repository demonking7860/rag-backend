#!/bin/bash
set -e

echo "Starting Django application..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done

echo "PostgreSQL is ready!"

# Check pgvector extension
echo "Checking pgvector extension..."
python << EOF
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
    exists = cursor.fetchone()[0]
    
    if not exists:
        print("ERROR: pgvector extension not found!")
        print("Please install pgvector extension in your PostgreSQL database.")
        sys.exit(1)
    else:
        print("✓ pgvector extension found")
EOF

if [ $? -ne 0 ]; then
    echo "CRITICAL: pgvector extension validation failed"
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

