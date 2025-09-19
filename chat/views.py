from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models import Q
import logging

from .models import Message
from .serializers import MessageSerializer, SendMessageSerializer

logger = logging.getLogger(__name__)

User = get_user_model()


class SendMessageView(generics.CreateAPIView):
    """Send a message (both users and admins use this)"""
    serializer_class = SendMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.save(sender=request.user)
        
        # Send email notification
        try:
            if request.user.is_superuser:
                # Admin sent message - no notification needed
                pass
            else:
                # User sent message - notify admin
                self.send_admin_notification(message)
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
        
        return Response({
            'success': True,
            'message': 'Message sent successfully',
            'data': MessageSerializer(message).data
        }, status=status.HTTP_201_CREATED)
    
    def send_admin_notification(self, message):
        """Send email to admin when user sends message"""
        admins = User.objects.filter(is_superuser=True, is_active=True)
        admin_emails = [admin.email for admin in admins if admin.email]
        
        if not admin_emails:
            return
        
        subject = f"New Customer Message from {message.sender.get_full_name() or message.sender.username}"
        
        html_content = f"""
        <h2>New Customer Message</h2>
        <p><strong>From:</strong> {message.sender.get_full_name() or message.sender.username}</p>
        <p><strong>Email:</strong> {message.sender.email}</p>
        <p><strong>Message:</strong></p>
        <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #007cba;">
            {message.message}
        </div>
        <p><small>Sent at: {message.created_at}</small></p>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"New message from {message.sender.username}: {message.message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)


class GetMessagesView(generics.ListAPIView):
    """Get all messages - different view based on user type"""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination to get all messages
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            # Admin sees all messages, ordered by creation time
            return Message.objects.all().select_related('sender').order_by('created_at')
        else:
            # Regular user sees only messages involving them
            return Message.objects.filter(
                Q(sender=self.request.user) | 
                Q(sender__is_superuser=True)  # Messages from any admin
            ).select_related('sender').order_by('created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)  # Return data directly, not wrapped in pagination


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request):
    """Mark messages as read"""
    message_ids = request.data.get('message_ids', [])
    
    if request.user.is_superuser:
        # Admin can mark any message as read
        messages = Message.objects.filter(id__in=message_ids)
    else:
        # Users can only mark messages sent to them as read
        messages = Message.objects.filter(
            id__in=message_ids,
            sender__is_superuser=True  # Only admin messages
        )
    
    updated = messages.update(is_read=True)
    
    return Response({
        'success': True,
        'message': f'Marked {updated} messages as read'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """Get count of unread messages"""
    if request.user.is_superuser:
        # Admin: count unread messages from users
        count = Message.objects.filter(
            is_from_admin=False,
            is_read=False
        ).count()
    else:
        # User: count unread messages from admins
        count = Message.objects.filter(
            sender__is_superuser=True,
            is_read=False
        ).count()
    
    return Response({
        'success': True,
        'unread_count': count
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    """Delete a message (admin only)"""
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        message = Message.objects.get(id=message_id)
        message.delete()
        return Response({
            'success': True,
            'message': 'Message deleted successfully'
        })
    except Message.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Message not found'
        }, status=status.HTTP_404_NOT_FOUND)