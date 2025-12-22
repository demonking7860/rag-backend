"""
Check if a file has chunks and why retrieval might be failing.
Usage: python manage.py shell
Then: exec(open('config/check_file_chunks.py').read())
"""
from apps.files.models import FileAsset
from apps.rag.models import DocumentChunk

# Get the file (replace with your file ID or filename)
filename = "RESUME-1.pdf"
file_asset = FileAsset.objects.filter(filename=filename).first()

if not file_asset:
    print(f"File '{filename}' not found")
    print("\nAvailable files:")
    for f in FileAsset.objects.all():
        print(f"  - {f.filename} (ID: {f.id}, Status: {f.status}, Ingestion: {f.ingestion_status})")
else:
    print(f"\nFile: {file_asset.filename}")
    print(f"Status: {file_asset.status}")
    print(f"Ingestion Status: {file_asset.ingestion_status}")
    print(f"User ID: {file_asset.user_id}")
    print(f"Metadata: {file_asset.metadata}")
    
    # Check chunks
    chunks = DocumentChunk.objects.filter(file_id=file_asset.id)
    print(f"\nChunks found: {chunks.count()}")
    
    if chunks.exists():
        print("\nFirst chunk sample:")
        first_chunk = chunks.first()
        print(f"  - Text: {first_chunk.chunk_text[:100]}...")
        print(f"  - Has embedding: {bool(first_chunk.embedding)}")
        print(f"  - Embedding type: {type(first_chunk.embedding)}")
        if hasattr(first_chunk.embedding, '__len__'):
            print(f"  - Embedding length: {len(first_chunk.embedding)}")
    else:
        print("\n⚠️  No chunks found! File needs to be re-ingested.")
        print(f"   Run: POST /api/files/{file_asset.id}/retry-finalize/")

