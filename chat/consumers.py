# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from django.contrib.auth.models import AnonymousUser
# from django.core.exceptions import ObjectDoesNotExist
# from .models import Message
# from .serializers import MessageSerializer
# import logging

# logger = logging.getLogger(__name__)


# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Check authentication
#         if self.scope["user"] is AnonymousUser or not self.scope["user"].is_authenticated:
#             logger.warning("Unauthenticated user attempted WebSocket connection")
#             await self.close()
#             return

#         try:
#             # Create room groups
#             self.user_room = f"chat_user_{self.scope['user'].id}"
#             self.admin_room = "chat_admin"
            
#             # Join appropriate rooms based on user type
#             if self.scope["user"].is_superuser:
#                 # Admin joins admin room to see all messages
#                 await self.channel_layer.group_add(self.admin_room, self.channel_name)
#                 logger.info(f"Admin user {self.scope['user'].username} joined admin room")
#             else:
#                 # Regular user joins their personal room
#                 await self.channel_layer.group_add(self.user_room, self.channel_name)
#                 # Also add to admin room so admins can see their messages
#                 await self.channel_layer.group_add(self.admin_room, self.channel_name)
#                 logger.info(f"User {self.scope['user'].username} joined user room")

#             await self.accept()
            
#             # Send connection confirmation
#             await self.send(text_data=json.dumps({
#                 'type': 'connection_established',
#                 'message': 'Connected successfully'
#             }))
            
#         except Exception as e:
#             logger.error(f"Error in WebSocket connect: {str(e)}")
#             await self.close()

#     async def disconnect(self, close_code):
#         try:
#             # Leave all rooms
#             if hasattr(self, 'user_room'):
#                 await self.channel_layer.group_discard(self.user_room, self.channel_name)
#             if hasattr(self, 'admin_room'):
#                 await self.channel_layer.group_discard(self.admin_room, self.channel_name)
            
#             logger.info(f"User {getattr(self.scope.get('user'), 'username', 'Unknown')} disconnected")
#         except Exception as e:
#             logger.error(f"Error in WebSocket disconnect: {str(e)}")

#     async def receive(self, text_data):
#         try:
#             data = json.loads(text_data)
#             message_text = data.get('message', '').strip()
            
#             if not message_text:
#                 await self.send(text_data=json.dumps({
#                     'type': 'error',
#                     'error': 'Message cannot be empty'
#                 }))
#                 return

#             # Save message to database
#             message = await self.save_message(message_text)
            
#             if not message:
#                 await self.send(text_data=json.dumps({
#                     'type': 'error',
#                     'error': 'Failed to save message'
#                 }))
#                 return
            
#             # Serialize message
#             serialized_message = await self.serialize_message(message)

#             # Determine broadcast strategy
#             if self.scope["user"].is_superuser:
#                 # Admin message - broadcast to all connected clients in admin room
#                 await self.channel_layer.group_send(
#                     self.admin_room,
#                     {
#                         'type': 'chat_message',
#                         'message': serialized_message
#                     }
#                 )
#                 logger.info(f"Admin message from {self.scope['user'].username} broadcasted")
#             else:
#                 # User message - send to admin room (so admins can see it)
#                 await self.channel_layer.group_send(
#                     self.admin_room,
#                     {
#                         'type': 'chat_message', 
#                         'message': serialized_message
#                     }
#                 )
                
#                 # Also send back to user's room for confirmation
#                 await self.channel_layer.group_send(
#                     self.user_room,
#                     {
#                         'type': 'chat_message',
#                         'message': serialized_message
#                     }
#                 )
#                 logger.info(f"User message from {self.scope['user'].username} sent")

#         except json.JSONDecodeError:
#             logger.error("Invalid JSON received in WebSocket")
#             await self.send(text_data=json.dumps({
#                 'type': 'error',
#                 'error': 'Invalid JSON format'
#             }))
#         except Exception as e:
#             logger.error(f"Error processing WebSocket message: {str(e)}")
#             await self.send(text_data=json.dumps({
#                 'type': 'error',
#                 'error': f'Server error: {str(e)}'
#             }))

#     async def chat_message(self, event):
#         """Send message to WebSocket"""
#         try:
#             await self.send(text_data=json.dumps({
#                 'type': 'message',
#                 'data': event['message']
#             }))
#         except Exception as e:
#             logger.error(f"Error sending chat message: {str(e)}")

#     @database_sync_to_async
#     def save_message(self, message_text):
#         """Save message to database"""
#         try:
#             message = Message.objects.create(
#                 sender=self.scope["user"],
#                 message=message_text
#             )
#             logger.info(f"Message saved: ID {message.id} from {self.scope['user'].username}")
#             return message
#         except Exception as e:
#             logger.error(f"Error saving message: {str(e)}")
#             return None

#     @database_sync_to_async
#     def serialize_message(self, message):
#         """Serialize message for JSON response"""
#         try:
#             return {
#                 'id': message.id,
#                 'message': message.message,
#                 'sender': message.sender.id,
#                 'sender_name': message.sender.get_full_name() or message.sender.username,
#                 'sender_username': message.sender.username,
#                 'sender_email': message.sender.email,
#                 'is_from_admin': message.is_from_admin,
#                 'is_read': message.is_read,
#                 'created_at': message.created_at.isoformat(),
#             }
#         except Exception as e:
#             logger.error(f"Error serializing message: {str(e)}")
#             return None

# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from .models import Message, Conversation
from .serializers import MessageSerializer
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check authentication
        if self.scope["user"] is AnonymousUser or not self.scope["user"].is_authenticated:
            logger.warning("Unauthenticated user attempted WebSocket connection")
            await self.close()
            return

        try:
            if self.scope["user"].is_superuser:
                # Admin joins admin room to receive all conversation notifications
                self.room_name = "admin_chat"
                await self.channel_layer.group_add(self.room_name, self.channel_name)
                logger.info(f"Admin user {self.scope['user'].username} joined admin room")
            else:
                # Regular user joins their personal conversation room
                self.room_name = f"conversation_user_{self.scope['user'].id}"
                await self.channel_layer.group_add(self.room_name, self.channel_name)
                logger.info(f"User {self.scope['user'].username} joined personal room")

            await self.accept()
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected successfully',
                'user_type': 'admin' if self.scope["user"].is_superuser else 'user'
            }))
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Leave room
            if hasattr(self, 'room_name'):
                await self.channel_layer.group_discard(self.room_name, self.channel_name)
            
            logger.info(f"User {getattr(self.scope.get('user'), 'username', 'Unknown')} disconnected")
        except Exception as e:
            logger.error(f"Error in WebSocket disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_text = data.get('message', '').strip()
            
            if not message_text:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': 'Message cannot be empty'
                }))
                return

            if self.scope["user"].is_superuser:
                # Admin sending message - need target user ID
                user_id = data.get('user_id')
                if not user_id:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'error': 'user_id is required for admin messages'
                    }))
                    return
                
                # Save message and get conversation
                result = await self.save_admin_message(message_text, user_id)
                if not result:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'error': 'Failed to send message'
                    }))
                    return
                
                message, target_user_id = result
                serialized_message = await self.serialize_message(message)
                
                # Send to admin room (for other admins and admin who sent it)
                await self.channel_layer.group_send(
                    "admin_chat",
                    {
                        'type': 'chat_message',
                        'message': serialized_message,
                        'conversation_id': message.conversation.id
                    }
                )
                
                # Send to target user's room if they're online
                await self.channel_layer.group_send(
                    f"conversation_user_{target_user_id}",
                    {
                        'type': 'chat_message',
                        'message': serialized_message,
                        'conversation_id': message.conversation.id
                    }
                )
                
                logger.info(f"Admin message sent to user {target_user_id}")
                
            else:
                # Regular user sending message to support
                message = await self.save_user_message(message_text)
                if not message:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'error': 'Failed to save message'
                    }))
                    return
                
                serialized_message = await self.serialize_message(message)
                
                # Send to user's own room (confirmation)
                await self.channel_layer.group_send(
                    f"conversation_user_{self.scope['user'].id}",
                    {
                        'type': 'chat_message',
                        'message': serialized_message,
                        'conversation_id': message.conversation.id
                    }
                )
                
                # Send to admin room (notification for all admins)
                await self.channel_layer.group_send(
                    "admin_chat",
                    {
                        'type': 'chat_message',
                        'message': serialized_message,
                        'conversation_id': message.conversation.id,
                        'is_new_user_message': True
                    }
                )
                
                logger.info(f"User message from {self.scope['user'].username} sent to admins")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received in WebSocket")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': f'Server error: {str(e)}'
            }))

    async def chat_message(self, event):
        """Send message to WebSocket"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'message',
                'data': event['message'],
                'conversation_id': event.get('conversation_id'),
                'is_new_user_message': event.get('is_new_user_message', False)
            }))
        except Exception as e:
            logger.error(f"Error sending chat message: {str(e)}")

    @database_sync_to_async
    def save_user_message(self, message_text):
        """Save message from user to support"""
        try:
            # Get or create conversation for this user
            conversation, created = Conversation.objects.get_or_create(
                user=self.scope["user"]
            )
            
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=self.scope["user"],
                message=message_text
            )
            
            logger.info(f"User message saved: ID {message.id} from {self.scope['user'].username}")
            return message
        except Exception as e:
            logger.error(f"Error saving user message: {str(e)}")
            return None

    @database_sync_to_async
    def save_admin_message(self, message_text, user_id):
        """Save message from admin to specific user"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get target user
            target_user = User.objects.get(id=user_id)
            
            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(
                user=target_user
            )
            
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=self.scope["user"],
                message=message_text
            )
            
            logger.info(f"Admin message saved: ID {message.id} to user {target_user.username}")
            return message, user_id
        except Exception as e:
            logger.error(f"Error saving admin message: {str(e)}")
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for JSON response"""
        try:
            return {
                'id': message.id,
                'conversation': message.conversation.id,
                'message': message.message,
                'sender': message.sender.id,
                'sender_name': message.sender.get_full_name() or message.sender.username,
                'sender_username': message.sender.username,
                'sender_email': message.sender.email,
                'is_from_admin': message.is_from_admin,
                'is_read': message.is_read,
                'created_at': message.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error serializing message: {str(e)}")
            return None