# AWS Bedrock Setup

## Required for:
- Image processing (Claude 3.5 Sonnet Vision)
- Text embeddings (Titan Text Embeddings v2)
- Chat responses (Claude 3.5 Sonnet)

## Setup Steps

### 1. Enable Bedrock in AWS Console

1. Go to AWS Bedrock Console: https://console.aws.amazon.com/bedrock/
2. Go to **Model access** in left sidebar
3. Enable these models:
   - **Titan Text Embeddings v2** (amazon.titan-embed-text-v2:0) - ✅ Already working!
   - **Claude 3.5 Sonnet** (anthropic.claude-3-5-sonnet-20240620-v1:0)
   - **Claude 3 Haiku** (anthropic.claude-3-haiku-20240307-v1:0) - for fallback

### 1a. Complete Anthropic Use Case Form (Required for Claude)

**Important:** Before using Claude models, you must:
1. Go to AWS Bedrock Console → **Model access**
2. Click on any Claude model (e.g., Claude 3.5 Sonnet)
3. Fill out the **Anthropic use case details form**
4. Wait 15 minutes after submission for access to be activated

**Current Status:**
- ✅ Titan Embeddings: Working
- ⏳ Claude Models: Waiting for use case form approval

### 2. IAM Permissions

Your AWS credentials need these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
                "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
            ]
        }
    ]
}
```

### 3. Verify Setup

Test Bedrock access:
```python
import boto3
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
# This should not raise an error if configured correctly
```

## Current Status

Without Bedrock:
- ✅ File upload works
- ✅ File listing works
- ❌ Image processing fails (will show error message)
- ❌ Embedding generation fails (file ingestion will fail)
- ❌ Chat responses fail (will show error message)

## Testing Without Bedrock

The app will work for basic file management, but RAG features require Bedrock.

