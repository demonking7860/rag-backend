# File-Chat RAG Chatbot

A full-stack RAG (Retrieval-Augmented Generation) chatbot application that allows users to upload documents, process them with AI, and chat about their content.

## Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Django + Django REST Framework
- **Database**: PostgreSQL with pgvector extension
- **Storage**: Amazon S3 (private bucket)
- **AI Services**: Amazon Bedrock (Claude 3.5 Sonnet, Titan Embeddings)

## Features

- **File Upload**: Direct S3 upload with pre-signed URLs (PDF, DOCX, TXT, PNG, JPEG)
- **In-Memory Processing**: All file processing happens in memory (no local disk storage)
- **RAG Pipeline**: Automatic text extraction, chunking, embedding, and vector storage
- **Chat Interface**: Ask questions about uploaded files with citations
- **User Authentication**: JWT-based authentication
- **File Management**: List, select, and delete files with pagination
- **Failure Handling**: Comprehensive error handling and retry mechanisms

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 12+ with pgvector extension
- AWS Account with:
  - S3 bucket (private)
  - Bedrock access (Claude 3.5 Sonnet, Titan Embeddings v2)
- AWS credentials (Access Key ID and Secret Access Key)

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

**Option 1: Using AWS Secrets Manager (Recommended for RDS)**

```env
# Database - AWS Secrets Manager
RDS_SECRET_NAME=rds!db-dc867e91-d63e-4af0-ad84-122afa8ff1de
RDS_SECRET_REGION=us-east-1
RDS_DB_HOST=database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com
RDS_DB_NAME=postgres

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Bedrock
BEDROCK_REGION=us-east-1

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_SECRET_KEY=your-jwt-secret-key

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Option 2: Direct DATABASE_URL (For local development)**

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Bedrock
BEDROCK_REGION=us-east-1

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_SECRET_KEY=your-jwt-secret-key

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Note**: 
- To find your RDS endpoint: AWS RDS Console → Select your database instance → Copy the "Endpoint" value
- **Important**: If your RDS instance is not publicly accessible (which is recommended for security), you'll need to:
  - Connect from an EC2 instance in the same VPC, OR
  - Use a VPN/bastion host, OR
  - Use AWS Systems Manager Session Manager for port forwarding
  - For local development, you may need to temporarily enable public accessibility or use a VPN

### 3. Setup PostgreSQL with pgvector

```sql
-- Connect to your PostgreSQL database
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Docker Deployment

### Backend

```bash
cd backend
docker build -t file-chat-backend .
docker run -p 8000:8000 --env-file .env file-chat-backend
```

## API Endpoints

### Authentication

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Refresh JWT token
- `GET /api/auth/me/` - Get current user

### Files

- `GET /api/files/` - List user's files (paginated)
- `POST /api/files/presign/` - Get pre-signed S3 upload URL
- `POST /api/files/finalize/` - Finalize upload and trigger ingestion
- `DELETE /api/files/{id}/` - Delete file (distributed delete)
- `POST /api/files/{id}/retry-finalize/` - Retry failed processing
- `POST /api/files/{id}/retry-chunks/` - Retry failed chunks (admin)
- `GET /api/files/deletion-failed/` - List files with deletion failures (admin)

### Chat

- `POST /api/chat/` - Send message and get response
- `GET /api/chat/history/{conversation_id}/` - Get conversation history

### Health

- `GET /api/health/` - Health check with pgvector validation

## Failure Policies

### Upload Succeeds, Finalize Fails

- FileAsset status set to `'uploaded'` (not `'ready'`)
- S3 object remains (recoverable)
- Frontend shows "Processing failed" with retry button
- Use `POST /api/files/{id}/retry-finalize/` to retry

### Partial Ingestion

- `ingestion_status` set to `'partial'`
- Partial chunks stored in DB
- Response includes warning with success/failure counts
- Admin endpoint to retry failed chunks

### DB Up but pgvector Missing

- Health check returns `503 Service Unavailable`
- Startup script validates pgvector before migrations
- Logs critical error for ops team

### Bedrock Down

- Retry with exponential backoff (3 attempts: 1s, 2s, 4s)
- If all retries fail, set `ingestion_status = 'failed'`
- Partial chunks preserved for later retry

### Claude Vision Response Empty

- Retry once with different prompt
- If still empty, store chunk with failure marker
- `extraction_method = 'image_vision_failed'`
- Log warning but don't fail entire ingestion

## Distributed Delete Sequence

1. **Delete Vectors**: Remove embeddings from pgvector
2. **Delete S3 Object**: Remove file from S3
3. **Delete DB Metadata**: Remove FileAsset record

If any step fails:
- Set `deletion_failed = True`
- Store error in metadata
- Return 500 with retry suggestion
- Admin endpoint lists all deletion-failed files

## Security

- All S3 operations use pre-signed URLs (no public access)
- Every database query includes `user_id` filter
- JWT authentication on all `/api/` routes (except `/auth/`)
- MIME type validation before S3 upload
- File size limits enforced (10MB max)
- CORS configured for frontend domain only

## Project Structure

```
django_Project/
├── backend/
│   ├── apps/
│   │   ├── accounts/      # Authentication
│   │   ├── files/         # File management & S3
│   │   ├── rag/           # RAG pipeline
│   │   └── chat/          # Chat functionality
│   ├── config/            # Django settings
│   ├── requirements.txt
│   ├── Dockerfile
│   └── startup.sh
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Development

### Running Tests

```bash
# Backend
cd backend
python manage.py test

# Frontend
cd frontend
npm test
```

### Code Formatting

```bash
# Backend
black .
isort .

# Frontend
npm run lint
```

## Troubleshooting

### pgvector Extension Not Found

```sql
-- Install pgvector extension
CREATE EXTENSION vector;
```

### S3 Upload Fails

- Check AWS credentials
- Verify S3 bucket exists and is accessible
- Check bucket CORS configuration if needed

### Bedrock Access Denied

- Verify Bedrock access in AWS IAM
- Check region configuration
- Ensure model IDs are correct

## License

MIT

