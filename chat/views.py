# from rest_framework import generics, status, permissions
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.contrib.auth import get_user_model

# from django.core.mail import EmailMultiAlternatives
# from django.conf import settings
# from django.db.models import Q
# import logging

# from .models import Message
# from .serializers import MessageSerializer, SendMessageSerializer

# logger = logging.getLogger(__name__)

# User = get_user_model()


# class SendMessageView(generics.CreateAPIView):
#     """Send a message (both users and admins use this)"""
#     serializer_class = SendMessageSerializer
#     permission_classes = [IsAuthenticated]
    
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         message = serializer.save(sender=request.user)
        
#         # Send email notification
#         try:
#             if request.user.is_superuser:
#                 # Admin sent message - no notification needed
#                 pass
#             else:
#                 # User sent message - notify admin
#                 self.send_admin_notification(message)
#         except Exception as e:
#             logger.error(f"Failed to send email notification: {e}")
        
#         return Response({
#             'success': True,
#             'message': 'Message sent successfully',
#             'data': MessageSerializer(message).data
#         }, status=status.HTTP_201_CREATED)
    
#     def send_admin_notification(self, message):
#         """Send email to admin when user sends message"""
#         admins = User.objects.filter(is_superuser=True, is_active=True)
#         admin_emails = [admin.email for admin in admins if admin.email]
        
#         if not admin_emails:
#             return
        
#         subject = f"New Customer Message from {message.sender.get_full_name() or message.sender.username}"
        
#         html_content = f"""
#         <h2>New Customer Message</h2>
#         <p><strong>From:</strong> {message.sender.get_full_name() or message.sender.username}</p>
#         <p><strong>Email:</strong> {message.sender.email}</p>
#         <p><strong>Message:</strong></p>
#         <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #007cba;">
#             {message.message}
#         </div>
#         <p><small>Sent at: {message.created_at}</small></p>
#         """
        
#         email = EmailMultiAlternatives(
#             subject=subject,
#             body=f"New message from {message.sender.username}: {message.message}",
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=admin_emails
#         )
#         email.attach_alternative(html_content, "text/html")
#         email.send(fail_silently=False)


# class GetMessagesView(generics.ListAPIView):
#     """Get all messages - different view based on user type"""
#     serializer_class = MessageSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = None  # Disable pagination to get all messages
    
#     def get_queryset(self):
#         if self.request.user.is_superuser:
#             # Admin sees all messages, ordered by creation time
#             return Message.objects.all().select_related('sender').order_by('created_at')
#         else:
#             # Regular user sees only messages involving them
#             return Message.objects.filter(
#                 Q(sender=self.request.user) | 
#                 Q(sender__is_superuser=True)  # Messages from any admin
#             ).select_related('sender').order_by('created_at')
    
#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)  # Return data directly, not wrapped in pagination


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def mark_messages_read(request):
#     """Mark messages as read"""
#     message_ids = request.data.get('message_ids', [])
    
#     if request.user.is_superuser:
#         # Admin can mark any message as read
#         messages = Message.objects.filter(id__in=message_ids)
#     else:
#         # Users can only mark messages sent to them as read
#         messages = Message.objects.filter(
#             id__in=message_ids,
#             sender__is_superuser=True  # Only admin messages
#         )
    
#     updated = messages.update(is_read=True)
    
#     return Response({
#         'success': True,
#         'message': f'Marked {updated} messages as read'
#     })


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_unread_count(request):
#     """Get count of unread messages"""
#     if request.user.is_superuser:
#         # Admin: count unread messages from users
#         count = Message.objects.filter(
#             is_from_admin=False,
#             is_read=False
#         ).count()
#     else:
#         # User: count unread messages from admins
#         count = Message.objects.filter(
#             sender__is_superuser=True,
#             is_read=False
#         ).count()
    
#     return Response({
#         'success': True,
#         'unread_count': count
#     })


# @api_view(['DELETE'])
# @permission_classes([IsAuthenticated])
# def delete_message(request, message_id):
#     """Delete a message (admin only)"""
#     if not request.user.is_superuser:
#         return Response({
#             'success': False,
#             'message': 'Admin access required'
#         }, status=status.HTTP_403_FORBIDDEN)
    
#     try:
#         message = Message.objects.get(id=message_id)
#         message.delete()
#         return Response({
#             'success': True,
#             'message': 'Message deleted successfully'
#         })
#     except Message.DoesNotExist:
#         return Response({
#             'success': False,
#             'message': 'Message not found'
#         }, status=status.HTTP_404_NOT_FOUND)

# views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
import logging

from .models import Message, Conversation
from .serializers import (
    MessageSerializer, 
    SendMessageSerializer, 
    ConversationSerializer,
    ConversationDetailSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()

class SendMessageView(generics.CreateAPIView):
    """Send a message in a conversation"""
    serializer_class = SendMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or create conversation
        if request.user.is_superuser:
            # Admin is sending to a specific user
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({
                    'success': False,
                    'error': 'user_id is required for admin messages'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                target_user = User.objects.get(id=user_id)
                conversation, created = Conversation.objects.get_or_create(
                    user=target_user
                )
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Regular user is sending to support
            conversation, created = Conversation.objects.get_or_create(
                user=request.user
            )
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            message=serializer.validated_data['message']
        )
        
        # Send email notification if needed
        try:
            if not request.user.is_superuser:
                # User sent message - notify admin
                self.send_admin_notification(message, conversation)
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
        
        return Response({
            'success': True,
            'message': 'Message sent successfully',
            'data': MessageSerializer(message).data
        }, status=status.HTTP_201_CREATED)
    
    def send_admin_notification(self, message, conversation):
        """Send email to admin when user sends message"""
        # admins = User.objects.filter(is_superuser=True, is_active=True)
        # admin_emails = [admin.email for admin in admins if admin.email]
        
        # if not admin_emails:
        #     return
        
        # subject = f"New Message from {conversation.user.get_full_name() or conversation.user.username}"
        
        # html_content = f"""
        # <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        #     <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center;">
        #         <h1 style="color: white; margin: 0;">💬 New Customer Message</h1>
        #     </div>
        #     <div style="padding: 20px; background: white; border: 1px solid #ddd;">
        #         <h2>Message Details</h2>
        #         <p><strong>From:</strong> {conversation.user.get_full_name() or conversation.user.username}</p>
        #         <p><strong>Email:</strong> {conversation.user.email}</p>
        #         <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #667eea; margin: 15px 0;">
        #             <p><strong>Message:</strong></p>
        #             <p>{message.message}</p>
        #         </div>
        #         <p><small>Sent at: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        #         <p><a href="https://your-admin-url.com/chat" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reply to Customer</a></p>
        #     </div>
        # </div>
        # """
        
        # email = EmailMultiAlternatives(
        #     subject=subject,
        #     body=f"New message from {conversation.user.username}: {message.message}",
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     to=admin_emails
        # )
        # email.attach_alternative(html_content, "text/html")
        # email.send(fail_silently=False)

# Admin views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """Get all conversations (admin only)"""
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    conversations = Conversation.objects.filter(is_active=True).select_related('user')
    serializer = ConversationSerializer(conversations, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, conversation_id=None):
    """Get messages for a specific conversation"""
    if request.user.is_superuser:
        # Admin can view any conversation
        if not conversation_id:
            return Response({
                'success': False,
                'error': 'conversation_id is required for admin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        conversation = get_object_or_404(Conversation, id=conversation_id)
        # Mark conversation as read when admin views it
        conversation.mark_as_read()
    else:
        # User can only view their own conversation
        conversation, created = Conversation.objects.get_or_create(
            user=request.user
        )
    
    messages = conversation.messages.all().select_related('sender')
    serializer = MessageSerializer(messages, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data,
        'conversation': ConversationSerializer(conversation).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """Get count of unread conversations/messages"""
    if request.user.is_superuser:
        # Admin: count conversations with unread messages
        count = Conversation.objects.filter(unread_count__gt=0).count()
        total_unread = sum(
            conv.unread_count for conv in 
            Conversation.objects.filter(unread_count__gt=0)
        )
        
        return Response({
            'success': True,
            'unread_conversations': count,
            'total_unread_messages': total_unread
        })
    else:
        # User: count unread messages from admin in their conversation
        try:
            conversation = Conversation.objects.get(user=request.user)
            count = conversation.messages.filter(
                is_from_admin=True,
                is_read=False
            ).count()
        except Conversation.DoesNotExist:
            count = 0
        
        return Response({
            'success': True,
            'unread_count': count
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request):
    """Mark messages as read"""
    if request.user.is_superuser:
        # Admin marking conversation as read
        conversation_id = request.data.get('conversation_id')
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
            conversation.mark_as_read()
            # Also mark individual messages as read
            conversation.messages.filter(is_read=False).update(is_read=True)
    else:
        # User marking admin messages as read
        try:
            conversation = Conversation.objects.get(user=request.user)
            conversation.messages.filter(
                is_from_admin=True,
                is_read=False
            ).update(is_read=True)
        except Conversation.DoesNotExist:
            pass
    
    return Response({
        'success': True,
        'message': 'Messages marked as read'
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    """Delete a message (admin only)"""
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        message = Message.objects.get(id=message_id)
        conversation = message.conversation
        
        # If this was the last message, update conversation's last message
        if conversation.last_message == message.message:
            prev_message = conversation.messages.exclude(id=message_id).last()
            if prev_message:
                conversation.update_last_message(prev_message.message)
            else:
                conversation.last_message = ""
                conversation.save()
        
        message.delete()
        return Response({
            'success': True,
            'message': 'Message deleted successfully'
        })
    except Message.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Message not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """Delete a conversation (admin only)"""
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        conversation.delete()
        return Response({
            'success': True,
            'message': 'Conversation deleted successfully'
        })
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)