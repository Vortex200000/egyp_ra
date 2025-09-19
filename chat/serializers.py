from rest_framework import serializers
from .models import Message
from django.contrib.auth.models import User

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'sender_username', 'message', 
                 'is_from_admin', 'is_read', 'created_at']
        read_only_fields = ['sender', 'is_from_admin', 'created_at']

class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['message']
