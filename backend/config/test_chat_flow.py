"""
Test the chat flow to diagnose issues.
Run: python manage.py shell
Then: exec(open('config/test_chat_flow.py').read())
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.files.models import FileAsset
from apps.rag.models import DocumentChunk
from apps.rag.services import generate_embeddings, retrieve_chunks
from django.contrib.auth.models import User

print("=" * 60)
print("Chat Flow Diagnostic")
print("=" * 60)

# Get first user
user = User.objects.first()
if not user:
    print("❌ No users found")
    exit(1)

print(f"\n✅ User: {user.username} (ID: {user.id})")

# Get files
files = FileAsset.objects.filter(user=user, status='ready')
print(f"\n✅ Ready files: {files.count()}")
for f in files:
    print(f"   - {f.filename} (ID: {f.id}, Status: {f.status}, Ingestion: {f.ingestion_status})")

# Check chunks
all_chunks = DocumentChunk.objects.filter(user=user)
print(f"\n✅ Total chunks in database: {all_chunks.count()}")

if all_chunks.count() > 0:
    sample = all_chunks.first()
    print(f"   Sample chunk:")
    print(f"   - File: {sample.file.filename}")
    print(f"   - Text length: {len(sample.chunk_text)}")
    print(f"   - Embedding type: {type(sample.embedding)}")
    if hasattr(sample.embedding, '__len__'):
        print(f"   - Embedding length: {len(sample.embedding)}")
    else:
        print(f"   - Embedding: {str(sample.embedding)[:100]}")

# Test embedding generation
print(f"\n🔍 Testing embedding generation...")
try:
    test_query = "test query"
    embeddings = generate_embeddings([test_query])
    if embeddings:
        print(f"✅ Embedding generated: {len(embeddings[0])} dimensions")
        query_embedding = embeddings[0]
        
        # Test retrieval
        print(f"\n🔍 Testing chunk retrieval...")
        file_ids = list(files.values_list('id', flat=True))[:1]  # Test with first file
        chunks = retrieve_chunks(query_embedding, user.id, file_ids if file_ids else None)
        print(f"✅ Retrieved {len(chunks)} chunks")
        if chunks:
            print(f"   Top chunk similarity: {chunks[0].get('similarity', 'N/A')}")
    else:
        print("❌ No embedding generated")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

