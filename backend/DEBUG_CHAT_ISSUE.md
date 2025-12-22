# Debugging Chat Failure

## Issue
Chat is failing for both images and text files with error: "I apologize, but I'm having trouble processing your request right now."

## Possible Causes

1. **No chunks in database** - Files may need to be re-ingested after PostgreSQL migration
2. **pgvector query failing** - VectorField format issue
3. **Bedrock models not enabled** - Claude models need to be enabled in AWS Bedrock console
4. **Embedding format issue** - Embeddings might not be stored correctly in VectorField

## Steps to Debug

### 1. Check if chunks exist
```bash
python manage.py shell
>>> from apps.rag.models import DocumentChunk
>>> from apps.files.models import FileAsset
>>> from django.contrib.auth.models import User
>>> user = User.objects.first()
>>> files = FileAsset.objects.filter(user=user, status='ready')
>>> for f in files:
...     chunks = DocumentChunk.objects.filter(file_id=f.id)
...     print(f"{f.filename}: {chunks.count()} chunks")
```

### 2. Check backend logs
Look for errors in Django console output:
- `[Chat]` - Chat service logs
- `[RAG]` - RAG service logs
- Bedrock errors

### 3. Re-ingest files if needed
If chunks don't exist or are in wrong format:
- Delete old chunks
- Re-upload files OR use "Re-process" button in frontend

### 4. Test Bedrock access
```bash
python config/test_bedrock.py
```

### 5. Check pgvector query
The system now has better error handling. Check logs for:
- `[RAG] pgvector query returned X chunks`
- Any pgvector errors

## Quick Fix

If files were uploaded before PostgreSQL migration:
1. Delete the files
2. Re-upload them (they'll be ingested with VectorField)

Or use the "Re-process" button in the frontend if available.

