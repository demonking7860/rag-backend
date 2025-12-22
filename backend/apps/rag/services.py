import io
import base64
import json
import time
import boto3
import logging
from typing import List, Tuple, Optional
from PyPDF2 import PdfReader
from docx import Document
from django.conf import settings
from django.db import transaction
# Using simple text splitter instead of langchain to avoid Python 3.14 compatibility issues
from apps.files.models import FileAsset
from apps.files.services import S3Service
from .models import DocumentChunk

logger = logging.getLogger(__name__)


def extract_text_from_s3(s3_key: str, file_type: str) -> str:
    """Extract text from S3 object using in-memory processing."""
    s3_service = S3Service()
    
    # Read S3 object body directly into memory
    response = s3_service.get_object(s3_key)
    file_bytes = response['Body'].read()
    
    # Process in memory using BytesIO
    if file_type.lower() == 'pdf':
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        text = "\n".join([page.extract_text() for page in pdf_reader.pages])
    elif file_type.lower() in ['docx', 'doc']:
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
    elif file_type.lower() == 'txt':
        text = file_bytes.decode('utf-8')
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    return text


def extract_text_from_image(s3_key: str) -> Tuple[str, str]:
    """Extract text from image using Claude 3.5 Sonnet Vision."""
    try:
        bedrock_client = boto3.client('bedrock-runtime', region_name=settings.BEDROCK_REGION)
    except Exception as e:
        logger.error(f"Failed to initialize Bedrock client: {str(e)}")
        return "[Image processing failed: Bedrock not configured]", 'image_vision_failed'
    
    s3_service = S3Service()
    
    # Read image from S3
    response = s3_service.get_object(s3_key)
    image_bytes = response['Body'].read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    # Determine media type from file extension
    media_type = 'image/png' if s3_key.lower().endswith('.png') else 'image/jpeg'
    
    # Structured prompt for Markdown output
    prompt = """Analyze this image and extract all text, tables, and structural information.

Return your analysis in Markdown format, preserving:
- Table structures using Markdown tables
- Headers and hierarchy using #, ##, ###
- Lists using - or 1.
- Code blocks if present
- Any text content with proper formatting

If the image contains no text, describe the scene, objects, and context in structured Markdown."""
    
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_base64}},
                {"type": "text", "text": prompt}
            ]
        }]
    }
    
    try:
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps(request_body)
        )
        result = json.loads(response['body'].read())
        markdown_text = result['content'][0]['text']
        
        # Failure policy: Empty vision response
        if not markdown_text or markdown_text.strip() == "":
            # Retry once with different prompt
            retry_prompt = "Extract all visible text, tables, and structured content from this image. Format as Markdown."
            request_body['messages'][0]['content'][1]['text'] = retry_prompt
            retry_response = bedrock_client.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                body=json.dumps(request_body)
            )
            retry_result = json.loads(retry_response['body'].read())
            markdown_text = retry_result['content'][0]['text']
            
            if not markdown_text or markdown_text.strip() == "":
                # Store with failure marker
                markdown_text = "[Image processing failed: No content extracted]"
                extraction_method = 'image_vision_failed'
            else:
                extraction_method = 'image_vision'
        else:
            extraction_method = 'image_vision'
            
        return markdown_text, extraction_method
    except Exception as e:
        logger.warning(f"Vision API error for {s3_key}: {str(e)}")
        return "[Image processing failed: API error]", 'image_vision_failed'


def chunk_text(text: str, metadata: dict = None) -> List[dict]:
    """Chunk text using recursive character splitting."""
    chunk_size = settings.CHUNK_SIZE
    chunk_overlap = settings.CHUNK_OVERLAP
    
    # Simple recursive text splitter implementation
    if len(text) <= chunk_size:
        chunks = [text]
    else:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to split at sentence boundary
            chunk = text[start:end]
            # Look for sentence endings
            last_period = chunk.rfind('. ')
            last_newline = chunk.rfind('\n\n')
            split_point = max(last_period, last_newline)
            
            if split_point > chunk_size * 0.5:  # Only use if not too early
                end = start + split_point + 1
                chunk = text[start:end]
            
            chunks.append(chunk)
            start = end - chunk_overlap  # Overlap for context
    
    # Handle edge cases: empty chunks, single-character chunks
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        if not chunk or len(chunk.strip()) == 0:
            # Merge with previous if exists
            if processed_chunks:
                processed_chunks[-1]['text'] += '\n' + chunk
            continue
        
        if len(chunk.strip()) == 1 and processed_chunks:
            # Merge single-character chunks with previous
            processed_chunks[-1]['text'] += chunk
            continue
        
        chunk_meta = (metadata or {}).copy()
        chunk_meta['chunk_index'] = i
        processed_chunks.append({
            'text': chunk,
            'metadata': chunk_meta,
        })
    
    return processed_chunks


def generate_embeddings(text_chunks: List[str], max_retries: int = 3) -> List[List[float]]:
    """Generate embeddings using Amazon Nova 2 Multimodal Embeddings with retry logic."""
    try:
        bedrock_client = boto3.client('bedrock-runtime', region_name=settings.BEDROCK_REGION)
    except Exception as e:
        logger.error(f"Failed to initialize Bedrock client: {str(e)}")
        raise ValueError("Bedrock is not configured. Please set up AWS Bedrock access.")
    
    # Nova 2 embedding dimension (1024 to match current VectorField setup)
    embedding_dimension = getattr(settings, 'NOVA_EMBEDDING_DIMENSION', 1024)
    
    all_embeddings = []
    
    # Process each chunk individually
    for text_chunk in text_chunks:
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                # Nova 2 Multimodal Embeddings API format
                request_body = {
                    'taskType': 'SINGLE_EMBEDDING',
                    'singleEmbeddingParams': {
                        'embeddingPurpose': 'GENERIC_INDEX',
                        'embeddingDimension': embedding_dimension,
                        'text': {
                            'truncationMode': 'END',
                            'value': text_chunk
                        }
                    }
                }
                
                response = bedrock_client.invoke_model(
                    modelId="amazon.nova-2-multimodal-embeddings-v1:0",
                    body=json.dumps(request_body),
                    contentType='application/json'
                )
                
                result = json.loads(response['body'].read())
                
                # Nova 2 returns embedding in nested structure: {'embeddings': [{'embeddingType': 'TEXT', 'embedding': [...]}]}
                if 'embeddings' in result and len(result['embeddings']) > 0:
                    embedding_obj = result['embeddings'][0]
                    if 'embedding' in embedding_obj:
                        embedding = embedding_obj['embedding']
                        all_embeddings.append(embedding)
                        logger.debug(f"[RAG] Generated embedding: {len(embedding)} dimensions")
                        break  # Success, exit retry loop
                    else:
                        raise ValueError("No 'embedding' field in embeddings array item")
                elif 'embedding' in result:
                    # Direct embedding field (fallback)
                    embedding = result['embedding']
                    all_embeddings.append(embedding)
                    logger.debug(f"[RAG] Generated embedding: {len(embedding)} dimensions")
                    break  # Success, exit retry loop
                else:
                    logger.error(f"[RAG] Unexpected response format: {list(result.keys())}")
                    raise ValueError(f"No embedding in response. Response keys: {list(result.keys())}")
                
            except Exception as e:
                if attempt == max_retries - 1:
                    # All retries failed
                    logger.error(f"Embedding generation failed after {max_retries} attempts: {str(e)}")
                    raise
                else:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.warning(f"Embedding attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
    
    logger.info(f"[RAG] Generated {len(all_embeddings)} embeddings using Nova 2")
    return all_embeddings


def retrieve_chunks(query_embedding: List[float], user_id: int, file_ids: Optional[List[int]] = None, top_k: int = None) -> List[dict]:
    """Retrieve relevant chunks using vector similarity search."""
    import json
    import numpy as np
    from django.conf import settings
    
    top_k = top_k or settings.TOP_K_CHUNKS
    
    # Build query with user_id filter (mandatory)
    query = DocumentChunk.objects.filter(user_id=user_id)
    
    if file_ids:
        query = query.filter(file_id__in=file_ids)
    
    # Check if using PostgreSQL with pgvector
    use_pgvector = settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'
    
    if use_pgvector:
        # Use pgvector for PostgreSQL
        try:
            from pgvector.django import CosineDistance
            logger.info(f"[RAG] Using pgvector for PostgreSQL, query_embedding type: {type(query_embedding)}, length: {len(query_embedding) if query_embedding else 0}")
            
            # Ensure query_embedding is a list (pgvector expects list)
            if not isinstance(query_embedding, list):
                query_embedding = list(query_embedding)
            
            # Execute pgvector query
            chunks = query.annotate(
                distance=CosineDistance('embedding', query_embedding)
            ).order_by('distance')[:top_k]
            
            # Convert to list to evaluate query
            chunks_list = list(chunks)
            logger.info(f"[RAG] pgvector query returned {len(chunks_list)} chunks")
            
            results = []
            for chunk in chunks_list:
                try:
                    distance = float(chunk.distance)
                    similarity = max(0, 1 - distance)
                    
                    if similarity >= settings.SIMILARITY_THRESHOLD:
                        results.append({
                            'chunk_id': chunk.id,
                            'text': chunk.chunk_text,
                            'file_id': chunk.file_id,
                            'filename': chunk.file.filename,
                            'page_number': chunk.page_number,
                            'chunk_index': chunk.chunk_index,
                            'similarity': similarity,
                            'metadata': chunk.metadata,
                        })
                except Exception as e:
                    logger.warning(f"[RAG] Error processing chunk {chunk.id}: {str(e)}", exc_info=True)
                    continue
            
            # RELIABLE FALLBACK: If no chunks above threshold, return top chunks anyway
            if not results and chunks_list:
                logger.info(
                    f"[RAG] No chunks above threshold ({settings.SIMILARITY_THRESHOLD}) with pgvector, "
                    f"but returning top {len(chunks_list)} chunks anyway (fallback mode)"
                )
                for chunk in chunks_list:
                    try:
                        distance = float(chunk.distance)
                        similarity = max(0, 1 - distance)
                        results.append({
                            'chunk_id': chunk.id,
                            'text': chunk.chunk_text,
                            'file_id': chunk.file_id,
                            'filename': chunk.file.filename,
                            'page_number': chunk.page_number,
                            'chunk_index': chunk.chunk_index,
                            'similarity': similarity,
                            'metadata': chunk.metadata,
                        })
                    except Exception as e:
                        logger.warning(f"[RAG] Error processing chunk in fallback: {str(e)}")
                        continue
            
            logger.info(f"[RAG] Returning {len(results)} chunks from pgvector search")
            return results
        except Exception as e:
            logger.error(f"[RAG] pgvector search failed: {str(e)}", exc_info=True)
            logger.warning(f"[RAG] Falling back to Python similarity calculation")
    
    # Fallback: Python-based cosine similarity for SQLite
    all_chunks = list(query.all())
    logger.info(f"[RAG] Retrieved {len(all_chunks)} total chunks from database for user {user_id}, file_ids: {file_ids}")
    
    if not all_chunks:
        logger.warning(f"[RAG] No chunks found in database for user {user_id}, file_ids: {file_ids}")
        return []
    
    # Calculate cosine similarity for each chunk
    query_vec = np.array(query_embedding)
    similarities = []
    
    logger.info(f"[RAG] Calculating similarity for {len(all_chunks)} chunks...")
    for chunk in all_chunks:
        try:
            # Parse embedding from TextField (stored as JSON string)
            if isinstance(chunk.embedding, str):
                chunk_embedding = json.loads(chunk.embedding)
            else:
                chunk_embedding = chunk.embedding
            
            chunk_vec = np.array(chunk_embedding)
            
            # Cosine similarity
            dot_product = np.dot(query_vec, chunk_vec)
            norm_query = np.linalg.norm(query_vec)
            norm_chunk = np.linalg.norm(chunk_vec)
            
            if norm_query > 0 and norm_chunk > 0:
                similarity = dot_product / (norm_query * norm_chunk)
            else:
                similarity = 0.0
            
            similarities.append({
                'chunk': chunk,
                'similarity': float(similarity)
            })
        except Exception as e:
            logger.warning(f"[RAG] Error calculating similarity for chunk {chunk.id}: {str(e)}", exc_info=True)
            continue
    
    # Sort by similarity and filter by threshold
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    if similarities:
        top_scores = [f"{s['similarity']:.3f}" for s in similarities[:5]]
        logger.info(f"[RAG] Top similarity scores: {top_scores}")
    
    # Build results with threshold filtering
    results = []
    for item in similarities[:top_k]:
        if item['similarity'] >= settings.SIMILARITY_THRESHOLD:
            chunk = item['chunk']
            results.append({
                'chunk_id': chunk.id,
                'text': chunk.chunk_text,
                'file_id': chunk.file_id,
                'filename': chunk.file.filename,
                'page_number': chunk.page_number,
                'chunk_index': chunk.chunk_index,
                'similarity': item['similarity'],
                'metadata': chunk.metadata,
            })
    
    # RELIABLE FALLBACK: If no chunks above threshold, return top chunks anyway
    # This ensures we always return something if chunks exist
    if not results and similarities:
        logger.info(
            f"[RAG] No chunks above threshold ({settings.SIMILARITY_THRESHOLD}), "
            f"but returning top {min(top_k, len(similarities))} chunks anyway (fallback mode). "
            f"Top similarity: {similarities[0]['similarity']:.3f}"
        )
        # Return top chunks regardless of threshold
        for item in similarities[:top_k]:
            chunk = item['chunk']
            results.append({
                'chunk_id': chunk.id,
                'text': chunk.chunk_text,
                'file_id': chunk.file_id,
                'filename': chunk.file.filename,
                'page_number': chunk.page_number,
                'chunk_index': chunk.chunk_index,
                'similarity': item['similarity'],
                'metadata': chunk.metadata,
            })
    
    if not results:
        top_similarity = similarities[0]['similarity'] if similarities else 0.0
        logger.warning(
            f"[RAG] No chunks found for user {user_id}, file_ids: {file_ids}. "
            f"Total chunks checked: {len(all_chunks)}, Top similarity: {top_similarity:.3f}"
        )
    else:
        logger.info(f"[RAG] Returning {len(results)} chunks for user {user_id} (threshold: {settings.SIMILARITY_THRESHOLD})")
        similarity_scores = [f"{r['similarity']:.3f}" for r in results]
        logger.debug(f"[RAG] Similarity scores: {similarity_scores}")
    
    return results


def delete_vectors(file_id: int, user_id: int):
    """Delete all vectors associated with a file."""
    try:
        deleted_count = DocumentChunk.objects.filter(file_id=file_id, user_id=user_id).delete()[0]
        logger.info(f"Deleted {deleted_count} chunks for file {file_id}")
        return deleted_count
    except Exception as e:
        logger.error(f"Error deleting vectors for file {file_id}: {str(e)}")
        raise


def ingest_file_async(file_id: int, retry_failed: bool = False):
    """Async file ingestion - process file and create chunks."""
    from django.db import connection
    
    file_asset = FileAsset.objects.get(id=file_id)
    
    try:
        file_asset.ingestion_status = 'in_progress'
        file_asset.status = 'processing'
        file_asset.save()
        
        # Delete existing chunks if retrying
        if retry_failed:
            DocumentChunk.objects.filter(file_id=file_id).delete()
        
        # Extract text based on file type
        if file_asset.file_type.lower() in ['png', 'jpeg', 'jpg']:
            text, extraction_method = extract_text_from_image(file_asset.s3_key)
            page_number = None
        else:
            text = extract_text_from_s3(file_asset.s3_key, file_asset.file_type)
            extraction_method = file_asset.file_type.lower()
            page_number = None  # Could be extracted from PDF metadata
        
        if not text or len(text.strip()) == 0:
            raise ValueError("No text extracted from file")
        
        # Chunk text
        chunks_data = chunk_text(text, metadata={'page_number': page_number})
        
        if not chunks_data:
            raise ValueError("No chunks created from text")
        
        # Generate embeddings
        text_chunks = [chunk['text'] for chunk in chunks_data]
        embeddings = generate_embeddings(text_chunks)
        
        if len(embeddings) != len(chunks_data):
            raise ValueError(f"Embedding count mismatch: {len(embeddings)} != {len(chunks_data)}")
        
        # Store chunks in database
        chunks_to_create = []
        succeeded = 0
        failed = 0
        
        # Check database backend for embedding storage format
        use_sqlite = settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'
        use_postgresql = settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'
        
        logger.info(f"[RAG] Storing embeddings: SQLite={use_sqlite}, PostgreSQL={use_postgresql}")
        
        for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
            try:
                # For SQLite, store embedding as JSON string
                # For PostgreSQL with pgvector, store as list (VectorField handles it)
                if use_sqlite:
                    embedding_value = json.dumps(embedding)
                else:
                    # PostgreSQL: VectorField accepts list directly
                    # Ensure it's a list of floats
                    if not isinstance(embedding, list):
                        embedding = list(embedding)
                    embedding_value = [float(x) for x in embedding]  # Ensure all are floats
                
                chunk = DocumentChunk(
                    user=file_asset.user,
                    file=file_asset,
                    chunk_text=chunk_data['text'],
                    embedding=embedding_value,
                    metadata=chunk_data['metadata'],
                    page_number=chunk_data['metadata'].get('page_number'),
                    chunk_index=i,
                    extraction_method=extraction_method,
                )
                chunks_to_create.append(chunk)
                succeeded += 1
            except Exception as e:
                logger.error(f"Error creating chunk {i} for file {file_id}: {str(e)}")
                failed += 1
        
        # Bulk create chunks
        if chunks_to_create:
            DocumentChunk.objects.bulk_create(chunks_to_create)
        
        # Update file status
        if failed > 0 and succeeded > 0:
            file_asset.ingestion_status = 'partial'
            file_asset.status = 'ready'
            file_asset.metadata['chunks_succeeded'] = succeeded
            file_asset.metadata['chunks_failed'] = failed
        elif failed == 0:
            file_asset.ingestion_status = 'complete'
            file_asset.status = 'ready'
        else:
            file_asset.ingestion_status = 'failed'
            file_asset.status = 'failed'
            file_asset.metadata['error'] = 'All chunks failed to process'
        
        file_asset.save()
        
        logger.info(f"File {file_id} ingestion completed: {succeeded} succeeded, {failed} failed")
        
    except Exception as e:
        logger.error(f"File ingestion failed for {file_id}: {str(e)}")
        file_asset.ingestion_status = 'failed'
        file_asset.status = 'failed'
        file_asset.metadata['error'] = str(e)
        file_asset.save()
        raise

