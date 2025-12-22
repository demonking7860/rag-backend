from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, ChatRequestSerializer
from .services import generate_chat_response

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """Send message and get response with citations."""
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    user_message = data['message']
    conversation_id = data.get('conversation_id')
    file_ids = data.get('file_ids', [])
    
    logger.info(f"[Chat View] Received chat request from user {request.user.id}, file_ids: {file_ids}, message: {user_message[:50]}...")
    
    # Validate file status if file_ids are provided
    if file_ids:
        from apps.files.models import FileAsset
        files = FileAsset.objects.filter(id__in=file_ids, user=request.user)
        
        if files.count() != len(file_ids):
            logger.warning(f"[Chat View] Some files not found or not owned by user. Requested: {file_ids}, Found: {list(files.values_list('id', flat=True))}")
            return Response({
                'error': 'One or more files not found or access denied.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if any files are still processing
        processing_files = files.filter(status='processing')
        if processing_files.exists():
            processing_names = list(processing_files.values_list('filename', flat=True))
            logger.warning(f"[Chat View] Files still processing: {processing_names}")
            return Response({
                'error': f'File(s) still processing: {", ".join(processing_names)}. Please wait for processing to complete.',
                'processing_files': processing_names
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if files are ready
        ready_files = files.filter(status__in=['ready', 'partial'])
        if ready_files.count() == 0:
            failed_files = files.filter(status='failed')
            if failed_files.exists():
                failed_names = list(failed_files.values_list('filename', flat=True))
                logger.warning(f"[Chat View] Files failed: {failed_names}")
                return Response({
                    'error': f'File(s) processing failed: {", ".join(failed_names)}. Please re-upload or retry processing.',
                    'failed_files': failed_names
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                logger.warning(f"[Chat View] Files not ready: {list(files.values_list('status', flat=True))}")
                return Response({
                    'error': 'Files are not ready for chat. Please wait for processing to complete.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"[Chat View] File validation passed. {ready_files.count()} file(s) ready for chat.")
    
    # Get or create conversation
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        logger.info(f"[Chat View] Using existing conversation: {conversation_id}")
    else:
        conversation = Conversation.objects.create(user=request.user)
        logger.info(f"[Chat View] Created new conversation: {conversation.id}")
    
    # Save user message
    user_msg = Message.objects.create(
        conversation=conversation,
        role='user',
        content=user_message,
        file_ids=file_ids
    )
    
    # Get conversation history
    history = Message.objects.filter(conversation=conversation).order_by('created_at')
    conversation_history = [
        {'role': msg.role, 'content': msg.content}
        for msg in history
    ]
    logger.info(f"[Chat View] Conversation history: {len(conversation_history)} messages")
    
    # Generate response
    try:
        logger.info(f"[Chat View] Calling generate_chat_response...")
        result = generate_chat_response(
            user_message=user_message,
            user_id=request.user.id,
            file_ids=file_ids if file_ids else None,
            conversation_history=conversation_history
        )
        logger.info(f"[Chat View] Response generated: {len(result.get('response', ''))} chars, {len(result.get('citations', []))} citations")
        
        # Extract file IDs from citations
        file_ids_from_citations = []
        if result.get('citations'):
            # Get file IDs from chunk filenames
            from apps.files.models import FileAsset
            for citation in result.get('citations', []):
                try:
                    file_asset = FileAsset.objects.get(
                        filename=citation.get('filename'),
                        user_id=request.user.id
                    )
                    file_ids_from_citations.append(file_asset.id)
                except FileAsset.DoesNotExist:
                    pass
        
        # Save assistant message
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=result['response'],
            file_ids=file_ids_from_citations
        )
        
        return Response({
            'conversation_id': conversation.id,
            'message': MessageSerializer(user_msg).data,
            'response': MessageSerializer(assistant_msg).data,
            'citations': result.get('citations', []),
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[Chat View] Chat error: {str(e)}", exc_info=True)
        return Response({
            'error': 'Failed to generate response',
            'conversation_id': conversation.id,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request, conversation_id):
    """Get conversation history."""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    serializer = ConversationSerializer(conversation)
    return Response(serializer.data, status=status.HTTP_200_OK)

