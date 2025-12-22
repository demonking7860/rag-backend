# Running the Backend

## Quick Start

### 1. Create .env file (if not exists)
```powershell
cd backend
Copy-Item env.example .env
```

### 2. Install Python dependencies
```powershell
pip install -r requirements.txt
```

### 3. Test RDS connection (optional)
```powershell
python config/test_secrets.py
```

### 4. Run migrations
```powershell
python manage.py migrate
```

### 5. Create superuser (optional)
```powershell
python manage.py createsuperuser
```

### 6. Start development server
```powershell
python manage.py runserver
```

Server runs at: http://localhost:8000

## First Time Setup

1. **Ensure RDS is accessible** (see RDS_PUBLIC_ACCESS_GUIDE.md if needed)
2. **Install pgvector extension**:
   ```sql
   -- Connect to your RDS database and run:
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. **Run migrations** to create tables
4. **Start server**

## Troubleshooting

- **Import errors**: Make sure all dependencies are installed
- **Database connection**: Check RDS connectivity and .env settings
- **Port 8000 in use**: Change port with `python manage.py runserver 8001`

