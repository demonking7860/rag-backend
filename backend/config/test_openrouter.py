"""
Test script to verify OpenRouter API access.
Run: python config/test_openrouter.py
"""
import os
import sys
import django
import requests

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("Testing OpenRouter API Configuration")
print("=" * 60)

# Check API key
openrouter_api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
if not openrouter_api_key:
    print("\n❌ OPENROUTER_API_KEY not found in settings")
    print("   Add OPENROUTER_API_KEY to your .env file")
    sys.exit(1)

print(f"\n✅ API Key found: {openrouter_api_key[:15]}...")

# Test models
model_options = [
    "openai/gpt-4o-mini",  # Fast and cost-effective
    "openai/gpt-4o",  # More capable
    "anthropic/claude-3.5-sonnet",  # High quality
    "google/gemini-2.0-flash-exp",  # Fast Google model
    "meta-llama/llama-3.1-70b-instruct",  # Open source option
]

print(f"\n🧪 Testing models...")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openrouter_api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/your-repo",
    "X-Title": "RAG Chatbot Test"
}

for model_id in model_options:
    try:
        print(f"\n   Testing: {model_id}...")
        
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Say hello in one word."}
            ],
            "max_tokens": 50,
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                response_text = result['choices'][0]['message']['content']
                print(f"   ✅ {model_id} working! Response: {response_text.strip()}")
                break  # Found working model
            else:
                print(f"   ⚠️  {model_id} returned empty response")
        elif response.status_code == 401:
            print(f"   ❌ Authentication failed - check API key")
            sys.exit(1)
        elif response.status_code == 429:
            print(f"   ⚠️  Rate limit for {model_id}, trying next...")
            continue
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
            print(f"   ❌ {model_id} failed: {error_msg}")
            continue
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ {model_id} request error: {str(e)}")
        continue
    except Exception as e:
        print(f"   ❌ {model_id} error: {str(e)}")
        continue
else:
    print("\n❌ All models failed")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ OpenRouter API is working!")
print("=" * 60)

