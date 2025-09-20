# from django.db import models
# from django.conf import settings

# from django.utils import timezone


# class Message(models.Model):
#     sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
#     message = models.TextField()
#     is_from_admin = models.BooleanField(default=False)
#     is_read = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         ordering = ['created_at']
    
#     def __str__(self):
#         return f"{self.sender.username}: {self.message[:50]}..."

#     def save(self, *args, **kwargs):
#         # Auto-set is_from_admin based on sender's superuser status
#         self.is_from_admin = self.sender.is_superuser
#         super().save(*args, **kwargs)

# models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Conversation(models.Model):
    """A conversation between a user and support"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    last_message = models.TextField(blank=True)
    last_message_at = models.DateTimeField(auto_now_add=True)
    unread_count = models.IntegerField(default=0)  # Unread messages count for admin
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        return f"Conversation with {self.user.get_full_name() or self.user.username}"

    def update_last_message(self, message_text):
        """Update the last message and timestamp"""
        self.last_message = message_text
        self.last_message_at = timezone.now()
        self.save()

    def mark_as_read(self):
        """Mark conversation as read (reset unread count)"""
        self.unread_count = 0
        self.save()

    def increment_unread(self):
        """Increment unread count when user sends a message"""
        self.unread_count += 1
        self.save()


class Message(models.Model):
    """Individual messages within a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_from_admin = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        # Set is_from_admin based on sender
        self.is_from_admin = self.sender.is_superuser
        super().save(*args, **kwargs)
        
        # Update conversation
        self.conversation.update_last_message(self.message)
        if not self.is_from_admin:
            # User sent message, increment unread for admin
            self.conversation.increment_unread()

    def __str__(self):
        return f"Message from {self.sender.username}: {self.message[:50]}..."