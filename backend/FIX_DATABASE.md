# Fix Database Connection

## Quick Fix: Comment Out RDS in .env

Edit `backend/.env` and comment out RDS settings:

```env
# Database - Comment these out for local development
# RDS_SECRET_NAME=rds!db-dc867e91-d63e-4af0-ad84-122afa8ff1de
# RDS_SECRET_REGION=us-east-1
# RDS_DB_HOST=database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com
# RDS_DB_NAME=postgres
```

Django will use SQLite automatically.

## Then Run:

```powershell
python manage.py migrate
python manage.py runserver
```

## To Use RDS Later:

1. Enable public access (see RDS_PUBLIC_ACCESS_GUIDE.md)
2. Uncomment RDS settings in .env
3. Restart server

