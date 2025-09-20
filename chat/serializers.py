# from rest_framework import serializers
# from .models import Message
# from django.contrib.auth.models import User

# class MessageSerializer(serializers.ModelSerializer):
#     sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
#     sender_username = serializers.CharField(source='sender.username', read_only=True)
    
#     class Meta:
#         model = Message
#         fields = ['id', 'sender', 'sender_name', 'sender_username', 'message', 
#                  'is_from_admin', 'is_read', 'created_at']
#         read_only_fields = ['sender', 'is_from_admin', 'created_at']

# class SendMessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Message
#         fields = ['message']
# serializers.py
from rest_framework import serializers
from .models import Message, Conversation
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'sender_username', 
                 'sender_email', 'message', 'is_from_admin', 'is_read', 'created_at']
        read_only_fields = ['sender', 'is_from_admin', 'created_at', 'conversation']

class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['message']

class ConversationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'user', 'user_name', 'user_username', 'user_email', 
                 'user_avatar', 'last_message', 'last_message_at', 'unread_count', 
                 'is_active', 'created_at']
    
    def get_user_avatar(self, obj):
        # Return user initials for avatar
        name = obj.user.get_full_name() or obj.user.username
        return name[0].upper() if name else "U"

class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'user', 'user_name', 'user_username', 'user_email',
                 'last_message', 'last_message_at', 'unread_count', 'is_active', 
                 'created_at', 'messages']