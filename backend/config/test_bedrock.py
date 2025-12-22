"""
Test script to verify AWS Bedrock access and configuration.
Run: python config/test_bedrock.py
"""
import os
import sys
import django
import boto3
import json

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Setup Django before importing settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

def test_bedrock_access():
    """Test Bedrock access and model availability."""
    print("=" * 60)
    print("Testing AWS Bedrock Configuration")
    print("=" * 60)
    
    # Check AWS credentials
    print("\n1. Checking AWS Credentials...")
    try:
        aws_access_key = settings.AWS_ACCESS_KEY_ID
        aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
        if aws_access_key and aws_secret_key:
            print(f"   ✓ AWS_ACCESS_KEY_ID: {aws_access_key[:10]}...")
            print(f"   ✓ AWS_SECRET_ACCESS_KEY: {'*' * 20}")
        else:
            print("   ✗ AWS credentials not found in settings")
            return False
    except Exception as e:
        print(f"   ✗ Error checking credentials: {str(e)}")
        return False
    
    # Check Bedrock region
    print(f"\n2. Checking Bedrock Region...")
    bedrock_region = settings.BEDROCK_REGION
    print(f"   ✓ BEDROCK_REGION: {bedrock_region}")
    
    # Test Bedrock client initialization
    print(f"\n3. Testing Bedrock Client Initialization...")
    try:
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=bedrock_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        print("   ✓ Bedrock client initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize Bedrock client: {str(e)}")
        print("\n   Possible issues:")
        print("   - AWS credentials are incorrect")
        print("   - Bedrock is not available in this region")
        print("   - IAM user doesn't have Bedrock permissions")
        return False
    
    # Test Nova 2 Multimodal Embeddings
    print(f"\n4. Testing Nova 2 Multimodal Embeddings...")
    try:
        test_text = "Hello, this is a test."
        request_body = {
            'taskType': 'SINGLE_EMBEDDING',
            'singleEmbeddingParams': {
                'embeddingPurpose': 'GENERIC_INDEX',
                'embeddingDimension': 1024,
                'text': {
                    'truncationMode': 'END',
                    'value': test_text
                }
            }
        }
        
        response = bedrock_client.invoke_model(
            modelId="amazon.nova-2-multimodal-embeddings-v1:0",
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        result = json.loads(response['body'].read())
        
        # Nova 2 returns: {'embeddings': [{'embeddingType': 'TEXT', 'embedding': [...]}]}
        if 'embeddings' in result and len(result['embeddings']) > 0:
            embedding_obj = result['embeddings'][0]
            if 'embedding' in embedding_obj:
                embedding_dim = len(embedding_obj['embedding'])
                print(f"   ✓ Nova 2 Embeddings working (dimension: {embedding_dim})")
            else:
                print("   ✗ No 'embedding' field in embeddings array")
                return False
        elif 'embedding' in result:
            embedding_dim = len(result['embedding'])
            print(f"   ✓ Nova 2 Embeddings working (dimension: {embedding_dim})")
        else:
            print("   ✗ No embedding in response")
            print(f"   Response keys: {list(result.keys())}")
            return False
    except bedrock_client.exceptions.AccessDeniedException:
        print("   ✗ Access Denied - Model not enabled or no permissions")
        print("\n   Solution:")
        print("   1. Go to AWS Bedrock Console")
        print("   2. Navigate to 'Model access'")
        print("   3. Enable 'Nova 2 Multimodal Embeddings'")
        return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    # Test Llama 3.1 70B Instruct
    print(f"\n5. Testing Llama 3.1 70B Instruct...")
    try:
        model_id = "meta.llama3-1-70b-instruct-v1:0"
        # Llama 3.1 requires inference profile ARN
        inference_profile_arn = f"arn:aws:bedrock:{bedrock_region}::inference-profile/meta.llama3-1-70b-instruct-v1:0"
        
        # Format prompt with [INST] tags
        prompt = "[INST] Say hello in one word. [/INST]"
        
        request_body = {
            "prompt": prompt,
            "max_gen_len": 100,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        # Try inference profile first (required)
        try:
            response = bedrock_client.invoke_model(
                modelId=inference_profile_arn,
                body=json.dumps(request_body)
            )
        except Exception as e:
            error_msg = str(e)
            if "inference profile" not in error_msg.lower():
                # Try direct model ID as fallback
                print(f"   Trying direct model ID...")
                response = bedrock_client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )
            else:
                raise
        
        result = json.loads(response['body'].read())
        
        if 'generation' in result:
            response_text = result['generation'].strip()
            print(f"   ✓ Llama 3.1 working (response: {response_text[:50]}...)")
        elif 'output' in result:
            response_text = result['output'].strip()
            print(f"   ✓ Llama 3.1 working (response: {response_text[:50]}...)")
        else:
            print(f"   ✗ No generation in response. Keys: {list(result.keys())}")
            return False
    except bedrock_client.exceptions.AccessDeniedException:
        print("   ✗ Access Denied - Model not enabled or no permissions")
        print("\n   Solution:")
        print("   1. Go to AWS Bedrock Console")
        print("   2. Navigate to 'Model access'")
        print("   3. Enable 'Llama 3.1 70B Instruct'")
        return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All Bedrock tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_bedrock_access()

