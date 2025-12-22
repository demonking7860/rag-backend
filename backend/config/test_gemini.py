"""
Test script to verify Google Gemini API access and list available models.
Run: python config/test_gemini.py
"""
import os
import sys
import django

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
import google.generativeai as genai

print("=" * 60)
print("Testing Google Gemini API Configuration")
print("=" * 60)

# Check API key
gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
if not gemini_api_key:
    print("\n❌ GEMINI_API_KEY not found in settings")
    print("   Add GEMINI_API_KEY to your .env file")
    sys.exit(1)

print(f"\n✅ API Key found: {gemini_api_key[:10]}...")

# Configure Gemini
try:
    genai.configure(api_key=gemini_api_key)
    print("✅ Gemini API configured successfully")
except Exception as e:
    print(f"❌ Failed to configure Gemini API: {str(e)}")
    sys.exit(1)

# List available models
print("\n📋 Listing available models...")
try:
    models = genai.list_models()
    available_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.replace('models/', '')
            available_models.append(model_name)
            print(f"   ✓ {model_name}")
    
    if not available_models:
        print("   ❌ No models found with generateContent support")
    else:
        print(f"\n✅ Found {len(available_models)} available model(s)")
        print(f"   Recommended: {available_models[0]}")
        
        # Test the first available model
        print(f"\n🧪 Testing model: {available_models[0]}...")
        try:
            model = genai.GenerativeModel(available_models[0])
            response = model.generate_content("Say hello in one word.")
            if response and response.text:
                print(f"   ✅ Model working! Response: {response.text.strip()}")
            else:
                print("   ❌ Empty response")
        except Exception as e:
            print(f"   ❌ Model test failed: {str(e)}")
            
except Exception as e:
    print(f"❌ Failed to list models: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

