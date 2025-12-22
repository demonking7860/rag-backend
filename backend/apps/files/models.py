from django.db import models
from django.contrib.auth.models import User


class FileAsset(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
        ('deletion_failed', 'Deletion Failed'),
    ]
    
    INGESTION_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('partial', 'Partial'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)  # pdf, docx, txt, png, jpeg
    s3_key = models.CharField(max_length=500, unique=True)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ingestion_status = models.CharField(max_length=20, choices=INGESTION_STATUS_CHOICES, default='not_started')
    deletion_failed = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)  # Store error messages, retry counts, etc.
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'ingestion_status']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.user.username})"

