from rest_framework import serializers
from .models import FileAsset


class FileAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAsset
        fields = [
            'id', 'filename', 'file_type', 'size', 'uploaded_at',
            'status', 'ingestion_status', 'deletion_failed', 'metadata'
        ]
        read_only_fields = ['id', 'uploaded_at', 'status', 'ingestion_status', 'deletion_failed', 'metadata']


class PresignRequestSerializer(serializers.Serializer):
    filename = serializers.CharField()
    file_type = serializers.CharField()
    size = serializers.IntegerField()


class FinalizeRequestSerializer(serializers.Serializer):
    s3_key = serializers.CharField()
    filename = serializers.CharField()
    file_type = serializers.CharField()
    size = serializers.IntegerField()


class FileUpdateSerializer(serializers.Serializer):
    filename = serializers.CharField(required=False, allow_blank=False, max_length=255)
    metadata = serializers.JSONField(required=False)
