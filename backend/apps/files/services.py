import boto3
import uuid
from datetime import timedelta
from django.conf import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3 operations."""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
    
    def generate_presigned_url(self, filename, file_type, size, user_id):
        """
        Generate pre-signed POST URL for direct S3 upload.
        Validates MIME type and file size.
        """
        # Validate file size
        if size > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / (1024*1024)}MB")
        
        # Validate MIME type
        mime_type_map = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'png': 'image/png',
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
        }
        
        mime_type = mime_type_map.get(file_type.lower())
        if not mime_type or mime_type not in settings.ALLOWED_MIME_TYPES:
            raise ValueError(f"File type {file_type} is not allowed")
        
        # Generate unique S3 key
        s3_key = f"uploads/{user_id}/{uuid.uuid4()}/{filename}"
        
        # Generate pre-signed POST URL (15 min expiry)
        try:
            conditions = [
                {'Content-Type': mime_type},
                ['content-length-range', 1, settings.MAX_FILE_SIZE],
            ]
            
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket,
                Key=s3_key,
                Fields={'Content-Type': mime_type},
                Conditions=conditions,
                ExpiresIn=900  # 15 minutes
            )
            
            return {
                'url': presigned_post['url'],
                'fields': presigned_post['fields'],
                's3_key': s3_key,
            }
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise
    
    def delete_s3_object(self, s3_key):
        """Delete object from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"Successfully deleted S3 object: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting S3 object {s3_key}: {str(e)}")
            raise
    
    def get_object(self, s3_key):
        """Get object from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            return response
        except ClientError as e:
            logger.error(f"Error getting S3 object {s3_key}: {str(e)}")
            raise

