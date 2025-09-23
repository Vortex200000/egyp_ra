# views.py (in your main app or create a new 'contact' app)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
import resend
import os
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated users to send contact emails
def send_contact_email(request):
    """
    API endpoint to send contact form emails to support
    """
    resend.api_key = os.environ["RESEND_API_KEY"]
    try:
        # Get form data
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        subject = request.data.get('subject', 'Contact Form Submission').strip()
        message = request.data.get('message', '').strip()
        
        # Validate required fields
        if not name or not email or not message:
            return Response({
                'error': 'Missing required fields',
                'message': 'Name, email, and message are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email format (basic validation)
        if '@' not in email or '.' not in email:
            return Response({
                'error': 'Invalid email format',
                'message': 'Please provide a valid email address.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create email subject with prefix
        email_subject = f'[CONTACT FORM] {subject}'
        
        # Create HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Contact Form Submission</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🏛️ EGYPET_RA TOURS</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Contact Form Submission</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #ddd; border-top: none;">
                <h2 style="color: #667eea; margin-top: 0;">New Contact Form Message 📩</h2>
                
                <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 25px 0;">
                    <h3 style="color: #667eea; margin-top: 0;">📋 Contact Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555; width: 120px;">Name:</td>
                            <td style="padding: 8px 0; color: #333;">{name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Email:</td>
                            <td style="padding: 8px 0; color: #333;"><a href="mailto:{email}" style="color: #667eea;">{email}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Subject:</td>
                            <td style="padding: 8px 0; color: #333;">{subject}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #555; margin-top: 0;">💬 Message:</h3>
                    <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                        <p style="margin: 0; color: #333; white-space: pre-wrap;">{message}</p>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="font-size: 14px; color: #6c757d; margin: 0;">
                        This message was sent from the EGYPET_RA TOURS contact form.
                    </p>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; border: 1px solid #ddd; border-top: none;">
                <p style="margin: 0; color: #6c757d; font-size: 14px;">
                    <strong style="color: #667eea;">EGYPET_RA TOURS</strong><br>
                    Contact Form Notification System
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        plain_content = f"""
New Contact Form Submission - EGYPET_RA TOURS
==============================================

CONTACT DETAILS:
Name: {name}
Email: {email}
Subject: {subject}

MESSAGE:
{message}

---
This message was sent from the EGYPET_RA TOURS contact form.
Please reply directly to {email} to respond to the customer.
        """
        # mimmosafari56@gmail.com
        # Create email message
        # email_message = EmailMultiAlternatives(
        #     subject=email_subject,
        #     body=plain_content,
        #     from_email=f"EGYPET_RA TOURS Contact Form <{settings.DEFAULT_FROM_EMAIL}>",
        #     to=['mimmosafari56@gmail.com'],  # Your support email
        #     reply_to=[email],  # Set customer email as reply-to
        #     headers={
        #         'X-Mailer': 'EGYPET_RA TOURS Contact System',
        #         'X-Priority': '3',
        #         'Importance': 'Normal'
        #     }
        # )
        params: resend.Emails.SendParams = {
    "from": "Acme <onboarding@resend.dev>",
    "to": ["delivered@resend.dev"],
    "subject": "hello world",
    "html": "<strong>it works!</strong>",
}
        email = resend.Emails.send(params)
        
        # Attach HTML version
        # email_message.attach_alternative(html_content, "text/html")
        
        # Send email
        # result = email_message.send(fail_silently=False)
        
        # if result:
        #     logger.info(f"Contact form email sent successfully from {email}")
        #     return Response({
        #         'success': True,
        #         'message': 'Your message has been sent successfully! We will get back to you within 24 hours.'
        #     }, status=status.HTTP_200_OK)
        # else:
        #     logger.warning(f"Contact form email sending returned False for {email}")
        #     return Response({
        #         'error': 'Email sending failed',
        #         'message': 'There was an issue sending your message. Please try again or contact us directly.'
        #     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Failed to send contact form email: {e}")
        return Response({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later or contact us directly.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Auto-reply function (optional)
def send_auto_reply_email(name, email):
    """
    Send an auto-reply confirmation to the customer
    """
    try:
        subject = 'Thank you for contacting EGYPET_RA TOURS! 🏛️'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Thank You</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🏛️ EGYPET_RA TOURS</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Thank You for Reaching Out!</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #ddd; border-top: none;">
                <h2 style="color: #667eea; margin-top: 0;">Message Received! ✅</h2>
                
                <p style="font-size: 16px;">Dear <strong>{name}</strong>,</p>
                
                <p style="font-size: 16px;">Thank you for contacting EGYPET_RA TOURS! We have received your message and will respond within 24 hours.</p>
                
                <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 25px 0;">
                    <p style="margin: 0; font-size: 16px;">In the meantime, feel free to explore our <strong>amazing tours</strong> and discover the wonders of Egypt!</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="font-size: 16px; margin: 0;">Need immediate assistance?</p>
                    <p style="margin: 10px 0;">
                        📞 <a href="tel:+201093706046" style="color: #667eea;">+20 109 370 6046</a><br>
                        📧 <a href="mailto:mimmosafari56@gmail.com" style="color: #667eea;">mimmosafari56@gmail.com</a>
                    </p>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; border: 1px solid #ddd; border-top: none;">
                <p style="margin: 0; color: #6c757d; font-size: 14px;">
                    Best regards,<br>
                    <strong style="color: #667eea;">EGYPET_RA TOURS Team</strong>
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_content = f"""
Dear {name},

Thank you for contacting EGYPET_RA TOURS! We have received your message and will respond within 24 hours.

In the meantime, feel free to explore our amazing tours and discover the wonders of Egypt!

Need immediate assistance?
Phone: +20 109 370 6046
Email: mimmosafari56@gmail.com

Best regards,
EGYPET_RA TOURS Team
        """
        
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=f"EGYPET_RA TOURS <{settings.DEFAULT_FROM_EMAIL}>",
            to=[email],
        )
        
        email_message.attach_alternative(html_content, "text/html")
        return email_message.send(fail_silently=True)
        
    except Exception as e:
        logger.error(f"Failed to send auto-reply email to {email}: {e}")
        return False


# Enhanced version with auto-reply
@api_view(['POST'])
@permission_classes([AllowAny])
def send_contact_email_with_auto_reply(request):
    """
    Enhanced version that also sends an auto-reply to the customer
    """
    try:
        # Get form data
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        subject = request.data.get('subject', 'Contact Form Submission').strip()
        message = request.data.get('message', '').strip()
        
        # Validate required fields
        if not name or not email or not message:
            return Response({
                'error': 'Missing required fields',
                'message': 'Name, email, and message are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send to support team
        support_email_sent = send_contact_email(request).status_code == 200
        
        # Send auto-reply to customer
        auto_reply_sent = send_auto_reply_email(name, email)
        
        if support_email_sent:
            return Response({
                'success': True,
                'message': 'Your message has been sent successfully! We will get back to you within 24 hours.',
                'auto_reply_sent': auto_reply_sent
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Email sending failed',
                'message': 'There was an issue sending your message. Please try again or contact us directly.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Failed to process contact form: {e}")
        return Response({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)