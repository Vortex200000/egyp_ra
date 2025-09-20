# urls.py (in your main app or add to your main project URLs)

from django.urls import path
from . import views

urlpatterns = [
    # Your existing URLs...
    
    # Contact form endpoints
    path('send/', views.send_contact_email, name='send_contact_email'),
    # Or use the enhanced version with auto-reply:
    # path('api/contact/send/', views.send_contact_email_with_auto_reply, name='send_contact_email'),
    
    # Your other URLs...
]
