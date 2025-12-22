# Quick Fix: Database Connection Timeout

## Problem
RDS is not publicly accessible, causing connection timeout.

## Solution 1: Use SQLite (Quick - For Development)

Edit your `.env` file and comment out RDS settings:

```env
# Database - Comment out RDS for local development
# RDS_SECRET_NAME=rds!db-dc867e91-d63e-4af0-ad84-122afa8ff1de
# RDS_SECRET_REGION=us-east-1
# RDS_DB_HOST=database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com
# RDS_DB_NAME=postgres
```

Django will automatically use SQLite (`db.sqlite3`) when RDS is not configured.

**Note:** SQLite doesn't support pgvector, so vector search won't work. Use this only for basic testing.

## Solution 2: Enable RDS Public Access (For Full Features)

Follow `RDS_PUBLIC_ACCESS_GUIDE.md` to:
1. Enable public access on RDS
2. Update security group to allow your IP

Then uncomment RDS settings in `.env`.

## After Fix

Run migrations:
```powershell
python manage.py migrate
```

Start server:
```powershell
python manage.py runserver
```

