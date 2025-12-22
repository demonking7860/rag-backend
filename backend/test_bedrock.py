#!/usr/bin/env python
"""
Test script to verify Bedrock access and functionality.
Run this to check if your AWS credentials and Bedrock setup are working.
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import boto3
import json
from django.conf import settings

def test_bedrock_access():
    """Test basic Bedrock access."""
    print("Testing Bedrock access...")
    
    try:
        bedrock_client = boto3.client('bedrock-runtime', region_name=settings.BEDROCK_REGION)
        print(f"[OK] Bedrock client created for region: {settings.BEDROCK_REGION}")
        return bedrock_client
    except Exception as e:
        print(f"[ERROR] Failed to create Bedrock client: {str(e)}")
        return None

def test_titan_embeddings(client):
    """Test Titan Text Embeddings v2."""
    print("\nTesting Titan Text Embeddings v2...")
    
    try:
        request_body = {
            "inputText": "This is a test sentence for embedding generation."
        }
        
        response = client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        
        if 'embedding' in result:
            embedding = result['embedding']
            print(f"[OK] Titan embeddings working! Dimension: {len(embedding)}")
            return True
        else:
            print("[ERROR] No embedding in response")
            return False
            
    except Exception as e:
        print(f"[ERROR] Titan embeddings failed: {str(e)}")
        return False

def test_claude_vision(client):
    """Test Claude 3.5 Sonnet Vision (with a simple text prompt)."""
    print("\nTesting Claude 3.5 Sonnet...")
    
    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello! Can you respond with 'Bedrock is working'?"}
                ]
            }]
        }
        
        response = client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        
        if 'content' in result and len(result['content']) > 0:
            response_text = result['content'][0]['text']
            print(f"[OK] Claude 3.5 Sonnet working! Response: {response_text}")
            return True
        else:
            print("[ERROR] No content in Claude response")
            return False
            
    except Exception as e:
        print(f"[ERROR] Claude 3.5 Sonnet failed: {str(e)}")
        return False

def main():
    print("=== Bedrock Configuration Test ===")
    print(f"AWS Region: {settings.AWS_S3_REGION_NAME}")
    print(f"Bedrock Region: {settings.BEDROCK_REGION}")
    print(f"AWS Access Key ID: {settings.AWS_ACCESS_KEY_ID[:10]}...")
    
    # Test Bedrock access
    client = test_bedrock_access()
    if not client:
        print("\n[FAILED] Cannot proceed without Bedrock access")
        return
    
    # Test individual services
    titan_ok = test_titan_embeddings(client)
    claude_ok = test_claude_vision(client)
    llama_ok = test_llama_chat(client)
    
    print("\n=== Summary ===")
    if titan_ok and claude_ok:
        print("[SUCCESS] Core Bedrock services are working!")
        if llama_ok:
            print("[SUCCESS] Llama 3.1 70B also working!")
        else:
            print("[INFO] Llama 3.1 70B not available (requires inference profile access)")
        print("Your RAG pipeline should work correctly.")
    else:
        print("[FAILED] Some Bedrock services failed.")
        print("Check your AWS permissions for Bedrock model access.")

if __name__ == "__main__":
    main()