# Debugging Chunk Retrieval

## Current Status
- File: Pave_Career_Report (1).pdf
- Status: ready
- Ingestion: complete
- Chunks: 11 chunks exist in database

## Issue
Chat returns "I cannot find information" even though chunks exist.

## Likely Causes
1. **Similarity threshold too high** - Currently 0.6, might be filtering out all chunks
2. **Embedding format mismatch** - Query embedding might not match chunk embeddings
3. **Retrieval logic issue** - Similarity calculation might be failing

## Fix Applied
- Lowered SIMILARITY_THRESHOLD from 0.6 to 0.1 (very permissive for testing)

## Next Steps
1. Check backend logs for similarity scores
2. Look for "[RAG] Top similarity scores" in logs
3. If scores are low (< 0.1), the embeddings might not be matching
4. If scores are high but still filtered, check the threshold logic

## To Check Logs
Look for these log messages:
- `[RAG] Retrieved X total chunks from database`
- `[RAG] Top similarity scores: [...]`
- `[RAG] No chunks found above similarity threshold`
- `[Chat] Retrieved X chunks`

