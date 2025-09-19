from django.db import models
from django.conf import settings

from django.utils import timezone


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    is_from_admin = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}..."

    def save(self, *args, **kwargs):
        # Auto-set is_from_admin based on sender's superuser status
        self.is_from_admin = self.sender.is_superuser
        super().save(*args, **kwargs)