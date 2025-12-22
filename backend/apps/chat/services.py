import json
import logging
import requests
from typing import List, Optional
from django.conf import settings
from apps.rag.services import retrieve_chunks, generate_embeddings

logger = logging.getLogger(__name__)


def generate_chat_response(
    user_message: str,
    user_id: int,
    file_ids: Optional[List[int]] = None,
    conversation_history: Optional[List[dict]] = None
) -> dict:
    """Generate chat response using RAG and Bedrock Claude."""
    
    logger.info(f"[Chat] Generating response for user {user_id}, file_ids: {file_ids}, message: {user_message[:50]}...")
    
    # Generate query embedding with retry
    query_embedding = None
    max_embedding_retries = 2
    for attempt in range(max_embedding_retries):
        try:
            logger.info(f"[Chat] Generating query embedding (attempt {attempt + 1}/{max_embedding_retries})...")
            query_embeddings = generate_embeddings([user_message])
            query_embedding = query_embeddings[0] if query_embeddings else None
            if query_embedding:
                logger.info(f"[Chat] Query embedding generated: {len(query_embedding)} dimensions")
                break
        except Exception as e:
            logger.error(f"[Chat] Error generating query embedding (attempt {attempt + 1}): {str(e)}", exc_info=True)
            if attempt == max_embedding_retries - 1:
                logger.warning(f"[Chat] All embedding generation attempts failed, will try keyword fallback")
    
    # Retrieve relevant chunks
    chunks = []
    citations = []
    
    if query_embedding:
        try:
            logger.info(f"[Chat] Retrieving chunks for user {user_id}, file_ids: {file_ids}")
            chunks = retrieve_chunks(query_embedding, user_id, file_ids)
            logger.info(f"[Chat] Retrieved {len(chunks)} chunks via vector search")
        except Exception as e:
            logger.error(f"[Chat] Error retrieving chunks: {str(e)}", exc_info=True)
    
    # RELIABLE FALLBACK: If vector search failed or returned no chunks, try keyword search
    if not chunks and file_ids:
        logger.info(f"[Chat] Vector search returned no chunks, trying keyword fallback...")
        try:
            from apps.rag.models import DocumentChunk
            from apps.files.models import FileAsset
            
            # Simple keyword search as fallback
            query_words = user_message.lower().split()
            query_words = [w for w in query_words if len(w) > 2]  # Filter short words
            
            if query_words:
                # Search in chunk text
                keyword_chunks = DocumentChunk.objects.filter(
                    user_id=user_id,
                    file_id__in=file_ids
                )
                
                # Find chunks containing any query words
                matching_chunks = []
                for chunk in keyword_chunks:
                    chunk_text_lower = chunk.chunk_text.lower()
                    matches = sum(1 for word in query_words if word in chunk_text_lower)
                    if matches > 0:
                        matching_chunks.append({
                            'chunk': chunk,
                            'match_score': matches / len(query_words)
                        })
                
                # Sort by match score and take top chunks
                matching_chunks.sort(key=lambda x: x['match_score'], reverse=True)
                top_matches = matching_chunks[:settings.TOP_K_CHUNKS]
                
                if top_matches:
                    logger.info(f"[Chat] Keyword fallback found {len(top_matches)} chunks")
                    chunks = [{
                        'chunk_id': item['chunk'].id,
                        'text': item['chunk'].chunk_text,
                        'file_id': item['chunk'].file_id,
                        'filename': item['chunk'].file.filename,
                        'page_number': item['chunk'].page_number,
                        'chunk_index': item['chunk'].chunk_index,
                        'similarity': item['match_score'],  # Use match score as similarity
                        'metadata': item['chunk'].metadata,
                    } for item in top_matches]
        except Exception as e:
            logger.error(f"[Chat] Keyword fallback failed: {str(e)}", exc_info=True)
    
    # Build unique citations by filename
    seen_filenames = set()
    for chunk in chunks:
        filename = chunk.get('filename')
        if filename and filename not in seen_filenames:
            citations.append({
                'filename': filename,
                'page_number': chunk.get('page_number')
            })
            seen_filenames.add(filename)
    logger.info(f"[Chat] Built {len(citations)} citations from {len(chunks)} chunks")
    
    # Build context from chunks
    if chunks:
        context = "\n\n".join([f"[From {chunk['filename']}]: {chunk['text']}" for chunk in chunks])
        logger.info(f"[Chat] Built context with {len(chunks)} chunks, context length: {len(context)} chars")
    else:
        context = None
        logger.warning(f"[Chat] No chunks found for user {user_id}, file_ids: {file_ids}")
    
    # Early return if no chunks found (before calling Bedrock)
    if not chunks or not context:
        logger.info(f"[Chat] No chunks available after all fallbacks, returning 'no information' message")
        return {
            'response': "I cannot find information about this in your files.",
            'citations': [],
            'chunks_used': 0
        }
    
    # Generate response using OpenRouter API
    # At this point, we know chunks exist (early return handled above)
    
    # Check API key
    openrouter_api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
    if not openrouter_api_key:
        logger.error("[Chat] OPENROUTER_API_KEY not configured")
        return {
            'response': "I apologize, but the AI service is not configured. Please set OPENROUTER_API_KEY in environment variables.",
            'citations': [],
            'chunks_used': 0
        }
    
    try:
        logger.info(f"[Chat] Initializing OpenRouter API...")
        logger.info(f"[Chat] Context length: {len(context) if context else 0} chars, Chunks: {len(chunks)}")
        
        # System prompt
        system_prompt = """You are a helpful assistant that answers questions based on the provided context from user's documents.

If the context contains relevant information, use it to answer the question accurately.
If the context does not contain relevant information, say "I cannot find information about this in your files."
Always cite which file(s) you used when providing information from the context.

Format citations as: [filename] or [filename, page X] if page numbers are available."""
        
        # Build messages for OpenRouter (OpenAI-compatible format)
        messages = []
        
        # Add system message
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add conversation history
        if conversation_history:
            logger.info(f"[Chat] Adding {len(conversation_history[-5:])} messages from conversation history")
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add current user message with context
        user_content = f"Context from documents:\n\n{context}\n\nUser question: {user_message}"
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        logger.debug(f"[Chat] OpenRouter messages prepared, count: {len(messages)}")
        
        response_text = None
        last_error = None
        
        # Try different models in order of preference
        # OpenRouter provides access to many models - using reliable ones
        model_options = [
            "openai/gpt-4o-mini",  # Fast and cost-effective
            "openai/gpt-4o",  # More capable
            "anthropic/claude-3.5-sonnet",  # High quality
            "google/gemini-2.0-flash-exp",  # Fast Google model
            "meta-llama/llama-3.1-70b-instruct",  # Open source option
        ]
        
        for model_id in model_options:
            try:
                logger.info(f"[Chat] Invoking OpenRouter model: {model_id}")
                
                # OpenRouter API endpoint
                url = "https://openrouter.ai/api/v1/chat/completions"
                
                headers = {
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/your-repo",  # Optional: for tracking
                    "X-Title": "RAG Chatbot"  # Optional: for tracking
                }
                
                payload = {
                    "model": model_id,
                    "messages": messages,
                    "max_tokens": 2048,
                    "temperature": 0.7,
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract response text
                    if 'choices' in result and len(result['choices']) > 0:
                        choice = result['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            response_text = choice['message']['content'].strip()
                        else:
                            raise ValueError("No content in response message")
                    else:
                        raise ValueError("No choices in response")
                    
                    if not response_text or len(response_text.strip()) == 0:
                        raise ValueError("Empty text in OpenRouter response")
                    
                    logger.info(f"[Chat] OpenRouter response received from {model_id}, length: {len(response_text)} chars")
                    logger.debug(f"[Chat] Response preview: {response_text[:200]}...")
                    break  # Success, exit loop
                    
                elif response.status_code == 401:
                    raise ValueError("Invalid API key or authentication failed")
                elif response.status_code == 429:
                    logger.warning(f"[Chat] Rate limit for {model_id}, trying next model...")
                    continue  # Try next model
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                    raise ValueError(f"API error: {error_msg}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"[Chat] Request error for {model_id}: {str(e)}, trying next model...")
                last_error = e
                continue  # Try next model
            except Exception as e:
                logger.warning(f"[Chat] Error with {model_id}: {str(e)}, trying next model...")
                last_error = e
                continue  # Try next model
        
        if not response_text:
            error_msg = str(last_error) if last_error else "All models failed"
            logger.error(f"[Chat] All OpenRouter models failed: {error_msg}", exc_info=True)
            
            # Check for common errors
            if 'API key' in error_msg or 'authentication' in error_msg.lower() or '401' in error_msg:
                return {
                    'response': "I apologize, but there's an issue with the AI service authentication. Please check the API key configuration.",
                    'citations': [],
                    'chunks_used': len(chunks)
                }
            elif 'quota' in error_msg.lower() or 'limit' in error_msg.lower() or '429' in error_msg:
                return {
                    'response': "I apologize, but the AI service has reached its usage limit. Please try again later.",
                    'citations': [],
                    'chunks_used': len(chunks)
                }
            else:
                return {
                    'response': f"I apologize, but I'm having trouble processing your request. Error: {error_msg[:150]}",
                    'citations': [],
                    'chunks_used': len(chunks)
                }
        
        # Use Bedrock's response - don't override it
        logger.info(f"[Chat] Returning response with {len(citations)} citations, {len(chunks)} chunks used")
        
        return {
            'response': response_text,
            'citations': citations,
            'chunks_used': len(chunks)
        }
        
    except Exception as e:
        logger.error(f"[Chat] Error generating chat response: {str(e)}", exc_info=True)
        # Return more detailed error for debugging
        error_msg = str(e)
        return {
            'response': f"I apologize, but I encountered an error: {error_msg[:150]}. Please check the logs for details.",
            'citations': [],
            'chunks_used': len(chunks) if chunks else 0
        }

