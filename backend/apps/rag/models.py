from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from apps.files.models import FileAsset

# Conditionally import VectorField based on database backend
try:
    from pgvector.django import VectorField
    USE_VECTOR_FIELD = settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'
except:
    USE_VECTOR_FIELD = False

if USE_VECTOR_FIELD:
    EmbeddingField = lambda **kwargs: VectorField(dimensions=1024, **kwargs)
else:
    # Use TextField for SQLite (store as JSON string)
    EmbeddingField = lambda **kwargs: models.TextField(**kwargs)


class DocumentChunk(models.Model):
    EXTRACTION_METHOD_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('txt', 'TXT'),
        ('image_vision', 'Image Vision'),
        ('image_vision_failed', 'Image Vision Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chunks')
    file = models.ForeignKey(FileAsset, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    embedding = EmbeddingField()  # VectorField for PostgreSQL, TextField for SQLite
    metadata = models.JSONField(default=dict)
    page_number = models.IntegerField(null=True, blank=True)
    chunk_index = models.IntegerField()  # Order within file
    extraction_method = models.CharField(max_length=50, choices=EXTRACTION_METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['file', 'chunk_index']
        indexes = [
            models.Index(fields=['user', 'file']),
            models.Index(fields=['file', 'chunk_index']),
        ]
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.file.filename}"

