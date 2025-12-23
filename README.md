# File-Chat RAG Chatbot

Small full-stack project where you can upload your own files (PDF, DOCX, TXT, images) and then chat with a bot that answers **only** from your content.

## Tech choices (why these)
- **S3 (private + presigned)**: keeps uploads off the app server and is easy to lock down.
- **Postgres + pgvector**: preferred in the spec; simple to host and keeps vectors with app data.
- **Nova embeddings (Bedrock)**: solid quality, 1024-dim matches the vector field.
- **OpenRouter LLMs (GPT-4o-mini/GPT-4o/Claude 3.5)**: one key, multiple strong models, easy to swap.

## How it works
1) Login/register and upload files (docs or images).  
2) Frontend uploads directly to S3 via presigned URL (no server disk).  
3) Backend reads from S3 in memory, extracts text or image description, chunks, embeds, and stores in Postgres.  
4) Chat searches the chunks, calls the LLM, and returns an answer with citations (filenames).  
5) You can rename files, delete them (vectors + S3 + DB), and the UI auto-refreshes file status. Chat shows sources; responses animate in a simple streaming style.

## Backend (Django)
```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env` (or use your own secure secrets manager):
```
DATABASE_URL=postgresql://user:password@localhost:5432/ragdb
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=us-east-1
BEDROCK_REGION=us-east-1
OPENROUTER_API_KEY=
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
JWT_SECRET_KEY=your-jwt-secret
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Ensure pgvector is installed:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Run migrations and start:
```bash
python manage.py migrate
python manage.py runserver
```

Backend runs on `http://localhost:8000`.

## Frontend (React)
```bash
cd frontend
npm install
```

Create `frontend/.env`:
```
VITE_API_BASE_URL=http://localhost:8000/api
```

Start dev server:
```bash
npm run dev
```

Frontend runs on `http://localhost:5173`.

## Key API routes
- Auth: `POST /auth/register/`, `POST /auth/login/`, `POST /auth/refresh/`, `GET /auth/me/`
- Files: `GET /api/files/`, `POST /api/files/presign/`, `POST /api/files/finalize/`, `PATCH /api/files/{id}/update/`, `DELETE /api/files/{id}/`
- Chat: `POST /api/chat/`, `GET /api/chat/history/`
- Health: `GET /api/health/`

## Demo flow
1. Register/login.  
2. Upload a PDF/DOCX/TXT or an image with text.  
3. Wait briefly; the file list auto-refreshes from uploaded → processing → ready.  
4. Rename a file (inline).  
5. Open chat, pick specific files or all, ask a question.  
6. See the streamed reply and “Sources:” with the filenames.  
7. Delete a file (removes vectors + S3 + DB).

This is a simple assignment-focused build prioritizing clarity over production hardening.

