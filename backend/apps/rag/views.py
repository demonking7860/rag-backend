from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint with pgvector validation."""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Check pgvector extension
        with connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
            pgvector_exists = cursor.fetchone()[0]
        
        if not pgvector_exists:
            logger.critical("pgvector extension not found in database")
            return Response({
                'status': 'unhealthy',
                'message': 'Vector database not configured',
                'database': 'connected',
                'pgvector': 'missing'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'pgvector': 'available'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'message': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

