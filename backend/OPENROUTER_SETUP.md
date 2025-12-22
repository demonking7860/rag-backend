# OpenRouter API Setup

## Configuration

The chat functionality now uses **OpenRouter API** which provides access to multiple LLM models.

### Models Used

1. **Embeddings**: `amazon.nova-2-multimodal-embeddings-v1:0` (AWS Bedrock)
   - Still using AWS Bedrock for embeddings
   - Dimension: 1024

2. **Chat**: OpenRouter API with multiple model options
   - Primary: `openai/gpt-4o-mini` (fast and cost-effective)
   - Fallback: `openai/gpt-4o`, `anthropic/claude-3.5-sonnet`, `google/gemini-2.0-flash-exp`, `meta-llama/llama-3.1-70b-instruct`
   - Automatically tries different models if one fails

## Setup Steps

### 1. Add API Key to .env

Add this line to your `.env` file:
```env
OPENROUTER_API_KEY=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
```

### 2. Restart Backend

After adding the API key, restart your Django backend:
```bash
python manage.py runserver
```

## How It Works

1. **Embeddings**: Files are still processed using AWS Bedrock Nova 2 embeddings
2. **Chat**: User queries are sent to OpenRouter API with context from retrieved chunks
3. **Model Selection**: The system tries multiple models in order:
   - `openai/gpt-4o-mini` (primary - fast and affordable)
   - `openai/gpt-4o` (more capable)
   - `anthropic/claude-3.5-sonnet` (high quality)
   - `google/gemini-2.0-flash-exp` (fast Google model)
   - `meta-llama/llama-3.1-70b-instruct` (open source)
4. **Response**: The first successful model response is returned

## Available Models

OpenRouter provides access to 400+ models. You can:
- View all models: https://openrouter.ai/models
- Change the model list in `backend/apps/chat/services.py` (model_options list)

## API Key Security

⚠️ **Important**: The API key is stored in `.env` file. Make sure:
- `.env` is in `.gitignore` (never commit it)
- Use environment variables in production
- Rotate keys if exposed

## Testing

Test the chat functionality by:
1. Upload a file
2. Wait for processing to complete
3. Send a chat message
4. Verify OpenRouter responds with information from your files

## Troubleshooting

### Error: "OPENROUTER_API_KEY not configured"
- Check that `.env` file has `OPENROUTER_API_KEY` set
- Restart the backend server

### Error: "Invalid API key" or "401"
- Verify the API key is correct
- Check if the key has expired or been revoked

### Error: "429" or "rate limit"
- You've reached the API usage limit
- Wait for rate limit reset or upgrade your plan
- The system will try other models automatically

### All models fail
- Check your OpenRouter account status
- Verify API key permissions
- Check OpenRouter status page

## Cost Management

OpenRouter charges per token. Monitor usage at:
- https://openrouter.ai/activity

The system uses `gpt-4o-mini` by default which is cost-effective.

