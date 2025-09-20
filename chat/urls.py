# from django.urls import path
# from . import views

# urlpatterns = [
#     path('send/', views.SendMessageView.as_view(), name='send_message'),
#     path('messages/', views.GetMessagesView.as_view(), name='get_messages'),
#     path('mark-read/', views.mark_messages_read, name='mark_read'),
#     path('unread-count/', views.get_unread_count, name='unread_count'),
#     path('delete/<int:message_id>/', views.delete_message, name='delete_message'),
# ]




# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Send message (both users and admins)
    path('send/', views.SendMessageView.as_view(), name='send_message'),
    
    # Admin endpoints
    path('conversations/', views.get_conversations, name='get_conversations'),
    path('conversation/<int:conversation_id>/messages/', views.get_conversation_messages, name='get_conversation_messages'),
    
    # User endpoint (get their own conversation)
    path('my-messages/', views.get_conversation_messages, name='get_my_messages'),
    
    # Common endpoints
    path('unread/', views.get_unread_count, name='get_unread_count'),
    path('mark-read/', views.mark_messages_read, name='mark_messages_read'),
    
    # Admin only endpoints
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('conversation/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
]