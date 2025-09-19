import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from .models import Message
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
            # Create room groups
            self.user_room = f"chat_user_{self.scope['user'].id}"
            self.admin_room = "chat_admin"
            
            # Join appropriate rooms based on user type
            if self.scope["user"].is_superuser:
                # Admin joins admin room to see all messages
                await self.channel_layer.group_add(self.admin_room, self.channel_name)
                logger.info(f"Admin user {self.scope['user'].username} joined admin room")
            else:
                # Regular user joins their personal room
                await self.channel_layer.group_add(self.user_room, self.channel_name)
                # Also add to admin room so admins can see their messages
                await self.channel_layer.group_add(self.admin_room, self.channel_name)
                logger.info(f"User {self.scope['user'].username} joined user room")

            await self.accept()
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected successfully'
            }))
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Leave all rooms
            if hasattr(self, 'user_room'):
                await self.channel_layer.group_discard(self.user_room, self.channel_name)
            if hasattr(self, 'admin_room'):
                await self.channel_layer.group_discard(self.admin_room, self.channel_name)
            
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

            # Save message to database
            message = await self.save_message(message_text)
            
            if not message:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': 'Failed to save message'
                }))
                return
            
            # Serialize message
            serialized_message = await self.serialize_message(message)

            # Determine broadcast strategy
            if self.scope["user"].is_superuser:
                # Admin message - broadcast to all connected clients in admin room
                await self.channel_layer.group_send(
                    self.admin_room,
                    {
                        'type': 'chat_message',
                        'message': serialized_message
                    }
                )
                logger.info(f"Admin message from {self.scope['user'].username} broadcasted")
            else:
                # User message - send to admin room (so admins can see it)
                await self.channel_layer.group_send(
                    self.admin_room,
                    {
                        'type': 'chat_message', 
                        'message': serialized_message
                    }
                )
                
                # Also send back to user's room for confirmation
                await self.channel_layer.group_send(
                    self.user_room,
                    {
                        'type': 'chat_message',
                        'message': serialized_message
                    }
                )
                logger.info(f"User message from {self.scope['user'].username} sent")

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
                'data': event['message']
            }))
        except Exception as e:
            logger.error(f"Error sending chat message: {str(e)}")

    @database_sync_to_async
    def save_message(self, message_text):
        """Save message to database"""
        try:
            message = Message.objects.create(
                sender=self.scope["user"],
                message=message_text
            )
            logger.info(f"Message saved: ID {message.id} from {self.scope['user'].username}")
            return message
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for JSON response"""
        try:
            return {
                'id': message.id,
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