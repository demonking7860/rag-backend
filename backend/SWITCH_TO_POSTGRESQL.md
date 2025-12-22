# Switching from SQLite to PostgreSQL

## Current Status
✅ PostgreSQL RDS is set up and tested
✅ Codebase already supports PostgreSQL via AWS Secrets Manager

## Steps to Switch

### 1. Ensure .env file has RDS configuration

Your `.env` file should have:
```env
RDS_SECRET_NAME=rds!db-dc867e91-d63e-4af0-ad84-122afa8ff1de
RDS_SECRET_REGION=us-east-1
RDS_DB_HOST=database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com
RDS_DB_NAME=postgres
```

### 2. Verify connection

The code will automatically use PostgreSQL if:
- `RDS_SECRET_NAME` is set
- `RDS_DB_HOST` is set

### 3. Run migrations on PostgreSQL

```bash
cd backend
python manage.py migrate
```

### 4. Install pgvector extension

Connect to PostgreSQL and run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Or use psql:
```bash
psql -h database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com -U postgres -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 5. (Optional) Migrate data from SQLite

If you have data in SQLite you want to keep:
1. Export from SQLite
2. Import to PostgreSQL
3. Or re-upload files (they'll be re-ingested)

## Verification

After switching, check:
- Django uses PostgreSQL (check logs on startup)
- Migrations ran successfully
- pgvector extension is installed
- Files can be uploaded and ingested

