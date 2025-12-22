# Amazon Nova Models Setup

## Models Used

1. **Embeddings**: `amazon.nova-2-multimodal-embeddings-v1:0`
   - ✅ Working correctly
   - Dimension: 1024 (matches VectorField)
   - API: `invoke_model` with JSON body

2. **Chat**: `amazon.nova-premier-v1:0`
   - ⚠️ Requires model access to be enabled
   - API: `converse` method
   - May require inference profile in some regions

## Setup Steps

### 1. Enable Nova Models in AWS Bedrock

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click on **"Model access"** in the left sidebar
3. Find and enable:
   - **Amazon Nova 2 Multimodal Embeddings** (`amazon.nova-2-multimodal-embeddings-v1:0`)
   - **Amazon Nova Premier** (`amazon.nova-premier-v1:0`)
4. Wait for model access to be granted (may take a few minutes)

### 2. Verify Model Access

Run the test script:
```bash
python config/test_bedrock.py
```

Expected output:
- ✅ Nova 2 Embeddings working
- ✅ Nova Premier working

### 3. Region Availability

- **Nova 2 Embeddings**: Available in `us-east-1`
- **Nova Premier**: Available in `us-east-1`, `us-east-2`, `us-west-2`

Make sure your `BEDROCK_REGION` in `.env` matches an available region.

## Current Status

- ✅ **Nova 2 Embeddings**: Configured and working
- ⚠️ **Nova Premier**: Code updated, but model access needs to be enabled

## Troubleshooting

### Error: "Invocation of model ID amazon.nova-premier-v1:0 with on-demand throughput isn't supported"

**Solution**: Enable the model in AWS Bedrock Console → Model access

### Error: "The provided model identifier is invalid"

**Possible causes**:
1. Model not enabled in your AWS account
2. Wrong region (model not available in that region)
3. IAM permissions missing

**Solution**:
1. Check model access in Bedrock Console
2. Verify region matches model availability
3. Check IAM permissions for Bedrock access

## Code Implementation

### Embeddings (Nova 2)
- File: `backend/apps/rag/services.py`
- Function: `generate_embeddings()`
- API Format: `invoke_model` with JSON body

### Chat (Nova Premier)
- File: `backend/apps/chat/services.py`
- Function: `generate_chat_response()`
- API Format: `converse` method with messages array

