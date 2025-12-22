# Google Gemini API Setup

## Configuration

The chat functionality now uses **Google Gemini API** instead of AWS Bedrock.

### Models Used

1. **Embeddings**: `amazon.nova-2-multimodal-embeddings-v1:0` (AWS Bedrock)
   - Still using AWS Bedrock for embeddings
   - Dimension: 1024

2. **Chat**: `gemini-1.5-flash` (Google Gemini)
   - Using Google Gemini API for chat responses
   - Fast and efficient model

## Setup Steps

### 1. Add API Key to .env

Add this line to your `.env` file:
```env
GEMINI_API_KEY=AIzaSyBEZMfP9MhTSFE-jI6rhLHDqv5bgx8MWpo
```

### 2. Install Dependencies

The `google-generativeai` package is already added to `requirements.txt` and installed.

### 3. Restart Backend

After adding the API key, restart your Django backend:
```bash
python manage.py runserver
```

## How It Works

1. **Embeddings**: Files are still processed using AWS Bedrock Nova 2 embeddings
2. **Chat**: User queries are sent to Google Gemini API with context from retrieved chunks
3. **Response**: Gemini generates responses based on the document context

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
4. Verify Gemini responds with information from your files

## Troubleshooting

### Error: "GEMINI_API_KEY not configured"
- Check that `.env` file has `GEMINI_API_KEY` set
- Restart the backend server

### Error: "API key" or "authentication"
- Verify the API key is correct
- Check if the key has expired or been revoked

### Error: "quota" or "limit"
- You've reached the API usage limit
- Wait for quota reset or upgrade your plan

