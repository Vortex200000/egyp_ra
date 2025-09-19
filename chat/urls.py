from django.urls import path
from . import views

urlpatterns = [
    path('send/', views.SendMessageView.as_view(), name='send_message'),
    path('messages/', views.GetMessagesView.as_view(), name='get_messages'),
    path('mark-read/', views.mark_messages_read, name='mark_read'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('delete/<int:message_id>/', views.delete_message, name='delete_message'),
]