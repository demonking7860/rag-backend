from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from .models import FileAsset
from .serializers import (
    FileAssetSerializer,
    PresignRequestSerializer,
    FinalizeRequestSerializer,
    FileUpdateSerializer,
)
from .services import S3Service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_files(request):
    """List user's files with pagination."""
    files = FileAsset.objects.filter(user=request.user)
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total = files.count()
    files_page = files[start:end]
    
    serializer = FileAssetSerializer(files_page, many=True)
    return Response({
        'results': serializer.data,
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_file(request, file_id):
    """Rename or update metadata for a file (user-scoped)."""
    file_asset = get_object_or_404(FileAsset, id=file_id, user=request.user)

    serializer = FileUpdateSerializer(data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    if 'filename' in data:
        file_asset.filename = data['filename']

    if 'metadata' in data:
        # Merge metadata while keeping existing keys
        current_meta = file_asset.metadata or {}
        current_meta.update(data['metadata'] or {})
        file_asset.metadata = current_meta

    file_asset.save()
    return Response(FileAssetSerializer(file_asset).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def presign_upload(request):
    """Generate pre-signed S3 URL for direct upload."""
    serializer = PresignRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    s3_service = S3Service()
    try:
        result = s3_service.generate_presigned_url(
            filename=serializer.validated_data['filename'],
            file_type=serializer.validated_data['file_type'],
            size=serializer.validated_data['size'],
            user_id=request.user.id
        )
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return Response({'error': 'Failed to generate upload URL'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalize_upload(request):
    """Confirm upload and trigger RAG ingestion."""
    serializer = FinalizeRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Create FileAsset record
    file_asset = FileAsset.objects.create(
        user=request.user,
        filename=data['filename'],
        file_type=data['file_type'],
        s3_key=data['s3_key'],
        size=data['size'],
        status='uploaded',
        ingestion_status='not_started',
    )
    
    # Trigger async ingestion
    try:
        from apps.rag.services import ingest_file_async
        import threading
        
        # Run ingestion in background thread
        def run_ingestion():
            try:
                ingest_file_async(file_asset.id)
                # Update status after successful ingestion
                file_asset.refresh_from_db()
                if file_asset.ingestion_status == 'complete':
                    file_asset.status = 'ready'
                    file_asset.save()
            except Exception as e:
                logger.error(f"Background ingestion failed for file {file_asset.id}: {str(e)}")
                file_asset.refresh_from_db()
                file_asset.status = 'failed'
                file_asset.ingestion_status = 'failed'
                file_asset.metadata['finalize_error'] = str(e)
                file_asset.save()
        
        # Start background thread
        thread = threading.Thread(target=run_ingestion, daemon=True)
        thread.start()
        
        # Set initial processing status
        file_asset.status = 'processing'
        file_asset.ingestion_status = 'in_progress'
        file_asset.save()
        
    except Exception as e:
        # Upload succeeded but finalize setup failed
        logger.error(f"Finalize setup failed for file {file_asset.id}: {str(e)}")
        file_asset.status = 'uploaded'  # Not 'ready'
        file_asset.metadata['finalize_error'] = str(e)
        file_asset.save()
        return Response({
            'error': 'Processing setup failed. Please retry.',
            'file_id': file_asset.id,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    serializer = FileAssetSerializer(file_asset)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request, file_id):
    """Distributed delete with rollback logic."""
    file_asset = get_object_or_404(FileAsset, id=file_id, user=request.user)
    
    # Step 1: Delete Vectors
    try:
        from apps.rag.services import delete_vectors
        delete_vectors(file_id, request.user.id)
    except Exception as e:
        logger.error(f"Vector deletion failed for file {file_id}: {str(e)}")
        file_asset.deletion_failed = True
        file_asset.metadata['delete_error'] = str(e)
        file_asset.save()
        return Response({"error": "Vector deletion failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Step 2: Delete S3 Object
    try:
        s3_service = S3Service()
        s3_service.delete_s3_object(file_asset.s3_key)
    except Exception as e:
        logger.error(f"S3 deletion failed for file {file_id}: {str(e)}")
        # Rollback: Mark for manual cleanup
        file_asset.deletion_failed = True
        file_asset.metadata['delete_error'] = f"S3 deletion failed: {str(e)}"
        file_asset.save()
        return Response({"error": "S3 deletion failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Step 3: Delete DB Metadata (only if steps 1 & 2 succeed)
    try:
        file_asset.delete()
        return Response({"message": "File deleted successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        # Vectors and S3 are already gone, log critical error
        logger.critical(f"DB deletion failed after successful vector/S3 deletion: {file_id}")
        return Response({"error": "Database deletion failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_finalize(request, file_id):
    """Retry failed finalization."""
    file_asset = get_object_or_404(FileAsset, id=file_id, user=request.user)
    
    if file_asset.status not in ['uploaded', 'failed']:
        return Response({'error': 'File is not in a retryable state'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from apps.rag.services import ingest_file_async
        import threading
        
        # Run ingestion in background thread
        def run_retry_ingestion():
            try:
                ingest_file_async(file_asset.id)
                # Update status after successful ingestion
                file_asset.refresh_from_db()
                if file_asset.ingestion_status == 'complete':
                    file_asset.status = 'ready'
                    file_asset.save()
            except Exception as e:
                logger.error(f"Retry ingestion failed for file {file_asset.id}: {str(e)}")
                file_asset.refresh_from_db()
                file_asset.status = 'failed'
                file_asset.ingestion_status = 'failed'
                file_asset.metadata['finalize_error'] = str(e)
                file_asset.save()
        
        # Start background thread
        thread = threading.Thread(target=run_retry_ingestion, daemon=True)
        thread.start()
        
        # Set processing status immediately
        file_asset.status = 'processing'
        file_asset.ingestion_status = 'in_progress'
        file_asset.metadata.pop('finalize_error', None)
        file_asset.save()
        
        return Response({'message': 'Processing restarted'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Retry finalize setup failed for file {file_id}: {str(e)}")
        file_asset.metadata['finalize_error'] = str(e)
        file_asset.save()
        return Response({'error': 'Failed to restart processing'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_chunks(request, file_id):
    """Retry failed chunks (admin only - simplified for now)."""
    file_asset = get_object_or_404(FileAsset, id=file_id, user=request.user)
    
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    if file_asset.ingestion_status != 'partial':
        return Response({'error': 'File does not have partial ingestion'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from apps.rag.services import ingest_file_async
        ingest_file_async(file_asset.id, retry_failed=True)
        return Response({'message': 'Chunk retry initiated'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Retry chunks failed for file {file_id}: {str(e)}")
        return Response({'error': 'Failed to retry chunks'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deletion_failed_files(request):
    """List files needing manual cleanup (admin only)."""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    files = FileAsset.objects.filter(deletion_failed=True)
    serializer = FileAssetSerializer(files, many=True)
    return Response(serializer.data)

