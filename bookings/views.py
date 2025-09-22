# bookings/views.py

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.db import models
import re
import logging

from .models import Booking, BookingStatusHistory, BookingCancellation
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    CreateBookingSerializer,
    UpdateBookingSerializer,
    CancelBookingSerializer,
    GuestBookingLookupSerializer
)

# Setup logging
logger = logging.getLogger(__name__)

class CreateBookingView(generics.CreateAPIView):
    """
    Create a new booking (supports both authenticated and guest users)
    """
    serializer_class = CreateBookingSerializer
    permission_classes = [IsAuthenticated]


    def send_owner_notification_email(booking, action_type, additional_info=None):
        """
        Send notification email to site owner about booking actions
        action_type: 'new_booking', 'cancellation', 'admin_confirmation', 'admin_decline'
        """
        try:
            owner_email = 'mimmosafari56@gmail.com'
            
            # Determine subject and content based on action type
            if action_type == 'new_booking':
                subject = f'New Booking - {booking.booking_reference}'
                action_text = 'A new booking has been created'
                status_color = '#007bff'  # Blue
            elif action_type == 'cancellation':
                subject = f'Booking Cancelled - {booking.booking_reference}'
                action_text = 'A booking has been cancelled'
                status_color = '#dc3545'  # Red
            elif action_type == 'admin_confirmation':
                subject = f'Booking Confirmed by Admin - {booking.booking_reference}'
                action_text = 'You have confirmed this booking'
                status_color = '#28a745'  # Green
            elif action_type == 'admin_decline':
                subject = f'Booking Declined by Admin - {booking.booking_reference}'
                action_text = 'You have declined this booking'
                status_color = '#ffc107'  # Yellow
            else:
                subject = f'Booking Update - {booking.booking_reference}'
                action_text = 'Booking status has been updated'
                status_color = '#6c757d'  # Gray

            # HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Booking Notification</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background: {status_color}; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;"> NATA STORIA TRAVEL</h2>
                    <p style="margin: 5px 0 0 0;">Booking Notification</p>
                </div>
                
                <div style="padding: 20px; background: white; border: 1px solid #ddd;">
                    <h3 style="color: {status_color}; margin-top: 0;">{action_text}</h3>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Booking Reference:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{booking.booking_reference}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Customer:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{booking.full_name}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Email:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{booking.email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Phone:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{booking.phone or 'Not provided'}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Tour:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{booking.tour.title}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Date:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{booking.preferred_date}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Time:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{booking.preferred_time or 'To be confirmed'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Travelers:</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{booking.number_of_travelers}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Total Amount:</td>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">${booking.total_amount} USD</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Status:</td>
                            <td style="padding: 10px; border: 1px solid #ddd; color: {status_color}; font-weight: bold;">{booking.booking_status.upper()}</td>
                        </tr>
                    </table>
                    
                    {f'<div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;"><strong>Additional Info:</strong> {additional_info}</div>' if additional_info else ''}
                    
                    {f'<div style="background: #f8f9ff; padding: 15px; border-radius: 5px; margin: 15px 0;"><strong>Special Requests:</strong> {booking.special_requests}</div>' if booking.special_requests else ''}
                    
                    <p style="margin-top: 20px; font-size: 14px; color: #666;">
                        Generated automatically by  NATA STORIA TRAVEL booking system on {timezone.now().strftime('%Y-%m-%d at %H:%M')}
                    </p>
                </div>
            </body>
            </html>
            """

            # Plain text version
            plain_content = f"""
    {action_text.upper()}

    Booking Details:
    ================
    Reference: {booking.booking_reference}
    Customer: {booking.full_name}
    Email: {booking.email}
    Phone: {booking.phone or 'Not provided'}
    Tour: {booking.tour.title}
    Date: {booking.preferred_date}
    Time: {booking.preferred_time or 'To be confirmed'}
    Travelers: {booking.number_of_travelers}
    Total: ${booking.total_amount} USD
    Status: {booking.booking_status.upper()}

    {f'Additional Info: {additional_info}' if additional_info else ''}
    {f'Special Requests: {booking.special_requests}' if booking.special_requests else ''}

    Generated on {timezone.now().strftime('%Y-%m-%d at %H:%M')}
     NATA STORIA TRAVEL Booking System
            """

            # Create and send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[owner_email],
                headers={
                    'X-Mailer': ' NATA STORIA TRAVEL Booking System',
                    'X-Priority': '3' if action_type == 'new_booking' else '2',  # Higher priority for new bookings
                }
            )
            
            email.attach_alternative(html_content, "text/html")
            result = email.send(fail_silently=False)
            
            if result:
                logger.info(f"Owner notification sent successfully for {action_type} - booking {booking.booking_reference}")
                return True
            else:
                logger.warning(f"Owner notification failed for {action_type} - booking {booking.booking_reference}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send owner notification for {action_type} - booking {booking.booking_reference}: {e}")
            return False



    def check_duplicate_booking(self, user, tour_id, preferred_date, email=None):
            """
            Check if the user already has an active booking for the same tour on the same date
            """
            # Define active booking statuses (exclude cancelled and completed)
            active_statuses = ['pending', 'confirmed']
            
            # For authenticated users, check by user
            if user and user.is_authenticated:
                existing_booking = Booking.objects.filter(
                    user=user,
                    tour_id=tour_id,
                    preferred_date=preferred_date,
                    booking_status__in=active_statuses
                ).first()
                
                if existing_booking:
                    return existing_booking
            
            # For guest users or as additional check, also check by email
            if email:
                existing_booking_by_email = Booking.objects.filter(
                    email=email,
                    tour_id=tour_id,
                    preferred_date=preferred_date,
                    booking_status__in=active_statuses
                ).first()
                
                if existing_booking_by_email:
                    return existing_booking_by_email
            
            return None
    def validate_email_address(self, email):
        """Validate email format and basic checks"""
        try:
            validate_email(email)
            # Additional checks for common fake/problematic domains
            problematic_domains = [
                'test.com', 'example.com', 'fake.com', 'dummy.com',
                'temp.com', 'invalid.com'
            ]
            domain = email.split('@')[1]
            if domain in problematic_domains:
                return False
            
            # Basic format validation
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                return False
                
            return True
        except (ValidationError, IndexError):
            return False

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
        
    #     # Get email from request data or user
    #     email = request.data.get('email', request.user.email)
        
    #     # Validate email address
    #     if not self.validate_email_address(email):
    #         return Response({
    #             'success': False,
    #             'message': 'Please provide a valid email address',
    #             'error_code': 'INVALID_EMAIL'
    #         }, status=status.HTTP_400_BAD_REQUEST)
        
    #     booking = serializer.save(
    #         user=request.user,
    #         email=email
    #     )
        
    #     # Send confirmation email with error handling
    #     email_sent = False
    #     email_error = None
        
    #     try:
    #         email_sent = self.send_booking_confirmation_email(booking)
    #     except Exception as e:
    #         email_error = str(e)
    #         logger.error(f"Failed to send confirmation email for booking {booking.booking_reference}: {e}")
        
    #     response_data = {
    #         'success': True,
    #         'message': 'Booking created successfully',
    #         'booking': BookingDetailSerializer(booking).data,
    #         'email_sent': email_sent
    #     }
        
    #     # Include email error in response if it failed
    #     if not email_sent and email_error:
    #         response_data['email_warning'] = 'Booking created but confirmation email could not be sent'
        
    #     return Response(response_data, status=status.HTTP_201_CREATED)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get email from request data or user
        email = request.data.get('email', request.user.email)
        
        # Validate email address
        if not self.validate_email_address(email):
            return Response({
                'success': False,
                'message': 'Please provide a valid email address',
                'error_code': 'INVALID_EMAIL'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract tour and date from validated data
        tour_id = serializer.validated_data['tour_id']
        preferred_date = serializer.validated_data['preferred_date']
        
        # Check for duplicate booking
        duplicate_booking = self.check_duplicate_booking(
            user=request.user,
            tour_id=tour_id,
            preferred_date=preferred_date,
            email=email
        )
        
        if duplicate_booking:
            return Response({
                'success': False,
                'message': 'You already have an active booking for this tour on this date',
                'error_code': 'DUPLICATE_BOOKING',
                'existing_booking': {
                    'booking_reference': duplicate_booking.booking_reference,
                    'booking_status': duplicate_booking.booking_status,
                    'created_at': duplicate_booking.created_at,
                    'tour_title': duplicate_booking.tour.title
                }
            }, status=status.HTTP_409_CONFLICT)
        
        booking = serializer.save(
            user=request.user,
            email=email
        )
        
        # Send confirmation email with error handling
        email_sent = False
        email_error = None
        
        try:
            email_sent = self.send_booking_confirmation_email(booking)
        except Exception as e:
            email_error = str(e)
            logger.error(f"Failed to send confirmation email for booking {booking.booking_reference}: {e}")
        
        response_data = {
            'success': True,
            'message': 'Booking created successfully',
            'booking': BookingDetailSerializer(booking).data,
            'email_sent': email_sent
        }
        
        # Include email error in response if it failed
        if not email_sent and email_error:
            response_data['email_warning'] = 'Booking created but confirmation email could not be sent'
        
        try:
            send_owner_notification_email(booking, 'new_booking')
        except Exception as e:
            logger.error(f"Failed to send owner notification for new booking {booking.booking_reference}: {e}")


        return Response(response_data, status=status.HTTP_201_CREATED)
    

    def send_booking_confirmation_email(self, booking):
        """Send booking confirmation email to customer with improved formatting"""
        try:
            subject = f'🎫 Booking Confirmation - {booking.booking_reference}'
            
            # Create HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Booking Confirmation</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">🏛️  NATA STORIA TRAVEL</h1>
                    <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Your Adventure Awaits!</p>
                </div>
                
                <div style="background: white; padding: 30px; border: 1px solid #ddd; border-top: none;">
                    <h2 style="color: #667eea; margin-top: 0;">Booking Confirmed! ✅</h2>
                    
                    <p style="font-size: 16px;">Dear <strong>{booking.full_name}</strong>,</p>
                    
                    <p style="font-size: 16px;">Thank you for choosing  NATA STORIA TRAVEL! Your booking has been confirmed and we're excited to show you the wonders of Egypt.</p>
                    
                    <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 25px 0;">
                        <h3 style="color: #667eea; margin-top: 0;">📋 Booking Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Booking Reference:</td>
                                <td style="padding: 8px 0; color: #333;">{booking.booking_reference}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Tour:</td>
                                <td style="padding: 8px 0; color: #333;">{booking.tour.title}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Date:</td>
                                <td style="padding: 8px 0; color: #333;">{booking.preferred_date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Time:</td>
                                <td style="padding: 8px 0; color: #333;">{booking.preferred_time or 'To be confirmed'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Travelers:</td>
                                <td style="padding: 8px 0; color: #333;">{booking.number_of_travelers}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555; font-size: 18px;">Total Amount:</td>
                                <td style="padding: 8px 0; color: #667eea; font-size: 18px; font-weight: bold;">${booking.total_amount} USD</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffeaa7; margin: 20px 0;">
                        <p style="margin: 0; color: #856404;"><strong>💳 Payment:</strong> You can pay on arrival or we'll contact you with payment options.</p>
                    </div>
                    
                    <p style="font-size: 16px;">We will contact you within 24 hours to confirm your booking details and provide any additional information you may need.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="font-size: 16px; margin: 0;">Questions? We're here to help!</p>
                        <p style="margin: 10px 0;">
                            📧 <a href="mailto:support@egypt-tours.com" style="color: #667eea;">support@egypt-tours.com</a><br>
                            📞 <a href="tel:+201234567890" style="color: #667eea;">+20 123 456 7890</a>
                        </p>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; border: 1px solid #ddd; border-top: none;">
                    <p style="margin: 0; color: #6c757d; font-size: 14px;">
                        Best regards,<br>
                        <strong style="color: #667eea;"> NATA STORIA TRAVEL Team</strong>
                    </p>
                    <p style="margin: 15px 0 0 0; color: #6c757d; font-size: 12px;">
                        This email was sent regarding your booking. Please keep this email for your records.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_content = f"""
Dear {booking.full_name},

Thank you for choosing  NATA STORIA TRAVEL! Your booking has been confirmed.

BOOKING DETAILS:
================
Booking Reference: {booking.booking_reference}
Tour: {booking.tour.title}
Date: {booking.preferred_date}
Time: {booking.preferred_time or 'To be confirmed'}
Number of Travelers: {booking.number_of_travelers}
Total Amount: ${booking.total_amount} USD

PAYMENT: You can pay on arrival or we'll contact you with payment options.

We will contact you within 24 hours to confirm your booking details and provide any additional information you may need.

Questions? Contact us:
Email: support@egypt-tours.com
Phone: +20 123 456 7890

Best regards,
 NATA STORIA TRAVEL Team

---
This email was sent regarding your booking. Please keep this email for your records.
            """
            
            # Create email message with both HTML and plain text
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_content,
                from_email=f" NATA STORIA TRAVEL <{settings.DEFAULT_FROM_EMAIL}>",
                to=[booking.email],
                headers={
                    'Reply-To': settings.DEFAULT_FROM_EMAIL,
                    'X-Mailer': ' NATA STORIA TRAVEL Booking System',
                    'X-Priority': '3',
                    'Importance': 'Normal'
                }
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            result = email.send(fail_silently=False)
            
            if result:
                logger.info(f"Confirmation email sent successfully to {booking.email} for booking {booking.booking_reference}")
                return True
            else:
                logger.warning(f"Email sending returned False for booking {booking.booking_reference}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send confirmation email for booking {booking.booking_reference}: {e}")
            raise e

class UserBookingListView(generics.ListAPIView):
    """
    List all bookings for the authenticated user
    """
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related('tour').order_by('-created_at')

class BookingDetailView(generics.RetrieveAPIView):
    """
    Get detailed information about a specific booking
    """
    serializer_class = BookingDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'booking_reference'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related('tour').prefetch_related(
            'travelers', 'status_history', 'payments', 'cancellation'
        )

class UpdateBookingView(generics.UpdateAPIView):
    """
    Update booking information (limited fields)
    """
    serializer_class = UpdateBookingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'booking_reference'

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            booking_status__in=['pending', 'confirmed']
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if booking can be modified
        if not instance.can_be_cancelled:
            return Response({
                'success': False,
                'message': 'This booking cannot be modified'
            }, status=status.HTTP_400_BAD_REQUEST)

        response = super().update(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Create status history entry
            BookingStatusHistory.objects.create(
                booking=instance,
                old_status=instance.booking_status,
                new_status=instance.booking_status,
                changed_by=request.user,
                reason='Booking details updated by customer'
            )

        return Response({
            'success': True,
            'message': 'Booking updated successfully',
            'booking': BookingDetailSerializer(instance).data
        })

class CancelBookingView(generics.GenericAPIView):
    """
    Cancel a booking
    """
    serializer_class = CancelBookingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'booking_reference'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        
        # Check if booking can be cancelled
        if not booking.can_be_cancelled:
            return Response({
                'success': False,
                'message': 'This booking cannot be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update booking status
        old_status = booking.booking_status
        booking.booking_status = 'cancelled'
        booking.cancellation_date = timezone.now()
        booking.save()

        # Create cancellation record
        cancellation = BookingCancellation.objects.create(
            booking=booking,
            reason=serializer.validated_data['reason'],
            reason_details=serializer.validated_data.get('reason_details', ''),
            cancelled_by=request.user,
            refund_amount=booking.total_amount  # Full refund by default
        )

        # Create status history
        BookingStatusHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status='cancelled',
            changed_by=request.user,
            reason=f"Cancelled: {cancellation.get_reason_display()}"
        )

        # Send cancellation email
        email_sent = False
        try:
            email_sent = self.send_cancellation_email(booking, cancellation)
        except Exception as e:
            logger.error(f"Failed to send cancellation email for booking {booking.booking_reference}: {e}")

        response_data = {
            'success': True,
            'message': 'Booking cancelled successfully',
            'booking': BookingDetailSerializer(booking).data,
            'email_sent': email_sent
        }
        try:
            cancellation_info = f"Reason: {cancellation.get_reason_display()}"
            if cancellation.reason_details:
                cancellation_info += f" - {cancellation.reason_details}"
            send_owner_notification_email(booking, 'cancellation', cancellation_info)
        except Exception as e:
            logger.error(f"Failed to send owner notification for cancellation {booking.booking_reference}: {e}")

        return Response(response_data)

    def send_cancellation_email(self, booking, cancellation):
        """Send cancellation confirmation email with improved formatting"""
        try:
            subject = f'🚫 Booking Cancellation - {booking.booking_reference}'
            
            # HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Booking Cancellation</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">🏛️  NATA STORIA TRAVEL</h1>
                    <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Booking Cancellation</p>
                </div>
                
                <div style="background: white; padding: 30px; border: 1px solid #ddd; border-top: none;">
                    <h2 style="color: #ff6b6b; margin-top: 0;">Booking Cancelled</h2>
                    
                    <p style="font-size: 16px;">Dear <strong>{booking.full_name}</strong>,</p>
                    
                    <p style="font-size: 16px;">We have processed your cancellation request. Here are the details:</p>
                    
                    <div style="background: #fff5f5; padding: 20px; border-radius: 8px; border-left: 4px solid #ff6b6b; margin: 25px 0;">
                        <h3 style="color: #ff6b6b; margin-top: 0;">📋 Cancellation Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Booking Reference:</td>
                                <td style="padding: 8px 0; color: #333;">{booking.booking_reference}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Tour:</td>
                                <td style="padding: 8px 0; color: #333;">{booking.tour.title}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Original Date:</td>
                                <td style="padding: 8px 0; color: #333;">{booking.preferred_date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Cancellation Reason:</td>
                                <td style="padding: 8px 0; color: #333;">{cancellation.get_reason_display()}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #555;">Refund Amount:</td>
                                <td style="padding: 8px 0; color: #28a745; font-weight: bold;">${cancellation.refund_amount} USD</td>
                            </tr>
                        </table>
                    </div>
                    
                 
                    
                    <p style="font-size: 16px;">We're sorry to see you cancel your tour. If you'd like to reschedule or book another tour in the future, we'd be happy to help!</p>
                    
                  
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; border: 1px solid #ddd; border-top: none;">
                    <p style="margin: 0; color: #6c757d; font-size: 14px;">
                        Best regards,<br>
                        <strong style="color: #ff6b6b;"> NATA STORIA TRAVEL Team</strong>
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_content = f"""
Dear {booking.full_name},

We have processed your booking cancellation request.

CANCELLATION DETAILS:
====================
Booking Reference: {booking.booking_reference}
Tour: {booking.tour.title}
Original Date: {booking.preferred_date}
Cancellation Reason: {cancellation.get_reason_display()}


We're sorry to see you cancel your tour. If you'd like to reschedule or book another tour in the future, we'd be happy to help!

Questions? Contact us:
Email: support@egypt-tours.com
Phone: +20 123 456 7890

Best regards,
 NATA STORIA TRAVEL Team
            """
            
            # Create and send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_content,
                from_email=f" NATA STORIA TRAVEL <{settings.DEFAULT_FROM_EMAIL}>",
                to=[booking.email],
                headers={
                    'Reply-To': settings.DEFAULT_FROM_EMAIL,
                    'X-Mailer': ' NATA STORIA TRAVEL Booking System',
                }
            )
            
            email.attach_alternative(html_content, "text/html")
            result = email.send(fail_silently=False)
            
            if result:
                logger.info(f"Cancellation email sent successfully to {booking.email} for booking {booking.booking_reference}")
                return True
            else:
                logger.warning(f"Cancellation email sending returned False for booking {booking.booking_reference}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send cancellation email for booking {booking.booking_reference}: {e}")
            raise e

@api_view(['POST'])
@permission_classes([AllowAny])
def guest_booking_lookup(request):
    """
    Look up booking for guest users using booking reference and email
    """
    serializer = GuestBookingLookupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    booking = serializer.validated_data['booking']
    
    return Response({
        'success': True,
        'booking': BookingDetailSerializer(booking).data
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_guest_booking(request):
    """
    Cancel booking for guest users
    """
    # First lookup the booking
    lookup_serializer = GuestBookingLookupSerializer(data=request.data)
    lookup_serializer.is_valid(raise_exception=True)
    
    booking = lookup_serializer.validated_data['booking']
    
    # Check if booking can be cancelled
    if not booking.can_be_cancelled:
        return Response({
            'success': False,
            'message': 'This booking cannot be cancelled'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate cancellation data
    cancel_serializer = CancelBookingSerializer(data=request.data)
    cancel_serializer.is_valid(raise_exception=True)

    # Update booking status
    old_status = booking.booking_status
    booking.booking_status = 'cancelled'
    booking.cancellation_date = timezone.now()
    booking.save()

    # Create cancellation record
    cancellation = BookingCancellation.objects.create(
        booking=booking,
        reason=cancel_serializer.validated_data['reason'],
        reason_details=cancel_serializer.validated_data.get('reason_details', ''),
        refund_amount=booking.total_amount
    )

    # Create status history
    BookingStatusHistory.objects.create(
        booking=booking,
        old_status=old_status,
        new_status='cancelled',
        reason=f"Guest cancellation: {cancellation.get_reason_display()}"
    )

    return Response({
        'success': True,
        'message': 'Booking cancelled successfully',
        'booking': BookingDetailSerializer(booking).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_booking_stats(request):
    """
    Get booking statistics for the authenticated user
    """
    user_bookings = Booking.objects.filter(user=request.user)
    
    stats = {
        'total_bookings': user_bookings.count(),
        'confirmed_bookings': user_bookings.filter(booking_status='confirmed').count(),
        'completed_bookings': user_bookings.filter(booking_status='completed').count(),
        'cancelled_bookings': user_bookings.filter(booking_status='cancelled').count(),
        'pending_bookings': user_bookings.filter(booking_status='pending').count(),
        'total_spent': float(user_bookings.filter(payment_status='paid').aggregate(
            total=models.Sum('total_amount'))['total'] or 0),
        'upcoming_tours': user_bookings.filter(
            booking_status__in=['confirmed', 'pending'],
            preferred_date__gte=timezone.now().date()
        ).count()
    }
    
    return Response({
        'success': True,
        'stats': stats
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def upcoming_bookings(request):
    """
    Get upcoming bookings for the authenticated user
    """
    upcoming = Booking.objects.filter(
        user=request.user,
        booking_status__in=['confirmed', 'pending'],
        preferred_date__gte=timezone.now().date()
    ).select_related('tour').order_by('preferred_date')[:5]
    
    return Response({
        'success': True,
        'bookings': BookingListSerializer(upcoming, many=True).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_voucher(request, booking_reference):
    """
    Generate and download booking voucher as PDF
    """
    booking = get_object_or_404(Booking, booking_reference=booking_reference, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="voucher-{booking.booking_reference}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "🏛️  NATA STORIA TRAVEL")
    
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 80, "Tour Booking Voucher")

    # Booking details
    p.setFont("Helvetica", 14)
    y_pos = height - 120
    
    details = [
        f"Booking Reference: {booking.booking_reference}",
        f"Customer: {booking.full_name}",
        f"Email: {booking.email}",
        f"Tour: {booking.tour.title}",
        f"Location: {booking.tour.location}",
        f"Date: {booking.preferred_date}",
        f"Time: {booking.preferred_time or 'To be confirmed'}",
        f"Number of Travelers: {booking.number_of_travelers}",
    ]
    
    for detail in details:
        p.drawString(50, y_pos, detail)
        y_pos -= 25

    # Price section
    p.setFont("Helvetica-Bold", 16)
    y_pos -= 20
    p.drawString(50, y_pos, f"Total Price: ${booking.total_amount} USD")
    p.drawString(50, y_pos - 25, f"Payment Status: {booking.get_payment_status_display()}")

    # Instructions
    p.setFont("Helvetica", 12)
    y_pos -= 70
    instructions = [
        "IMPORTANT INSTRUCTIONS:",
        "• Please present this voucher to your tour guide on arrival",
        "• Arrive 15 minutes before your scheduled time",
        "• Bring a valid ID for all travelers",
        "• Contact us if you need to make any changes",
        "",
        "Contact Information:",
        "📧 Email: mimmosafari56@gmail.com",
        "📞 Phone: +20 109 370 6046",
        "🌐 Website: www.egypt-ra-tours.com"
    ]
    
    for instruction in instructions:
        if instruction.startswith("IMPORTANT"):
            p.setFont("Helvetica-Bold", 12)
        elif instruction.startswith("Contact"):
            p.setFont("Helvetica-Bold", 12)
        else:
            p.setFont("Helvetica", 11)
        
        p.drawString(50, y_pos, instruction)
        y_pos -= 18

    # Footer
    p.setFont("Helvetica", 10)
    p.drawString(50, 50, f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M')} •  NATA STORIA TRAVEL Booking System")

    p.showPage()
    p.save()
    
    logger.info(f"Voucher generated for booking {booking.booking_reference}")
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_all_bookings(request):
    """
    Admin endpoint to get all bookings with filtering options
    """
    # Check if user is admin
    if not request.user.is_staff:
        return Response({
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')  # all, pending, confirmed, cancelled
    
    # Base queryset
    bookings = Booking.objects.select_related('tour', 'user').order_by('-created_at')
    
    # Apply status filter
    if status_filter != 'all':
        bookings = bookings.filter(booking_status=status_filter)
    
    # Serialize bookings with extra admin info
    booking_data = []
    for booking in bookings:
        booking_info = {
            'id': booking.id,
            'booking_reference': booking.booking_reference,
            'customer_name': booking.full_name,
            'customer_email': booking.email,
            'tour_title': booking.tour.title,
            'tour_location': booking.tour.location,
            'preferred_date': booking.preferred_date,
            'preferred_time': booking.preferred_time,
            'number_of_travelers': booking.number_of_travelers,
            'total_amount': booking.total_amount,
            'phone_num':booking.phone , 
            'booking_status': booking.booking_status,
            'payment_status': booking.payment_status,
            'created_at': booking.created_at,
            'can_confirm': booking.booking_status == 'pending',
            'can_decline': booking.booking_status in ['pending', 'confirmed'],
            'special_requests': booking.special_requests,
            'user_id': booking.user.id if booking.user else None,
            'username': booking.user.username if booking.user else 'Guest',
        }
        booking_data.append(booking_info)
    
    return Response({
        'success': True,
        'bookings': booking_data,
        'total_count': len(booking_data)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_confirm_booking(request, booking_reference):
    """
    Admin endpoint to confirm a booking
    """
    # Check if user is admin
    if not request.user.is_staff:
        return Response({
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    booking = get_object_or_404(Booking, booking_reference=booking_reference)
    
    # Check if booking can be confirmed
    if booking.booking_status != 'pending':
        return Response({
            'error': f'Cannot confirm booking. Current status: {booking.booking_status}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update booking status
    booking.booking_status = 'confirmed'
    booking.confirmation_date = timezone.now()
    booking.save()
    
    # Create status history
    BookingStatusHistory.objects.create(
        booking=booking,
        old_status='pending',
        new_status='confirmed',
        changed_by=request.user,
        reason='Confirmed by admin'
    )
    
    # Send confirmation email
    email_sent = False
    try:
        email_sent = send_admin_confirmation_email(booking)
    except Exception as e:
        logger.error(f"Failed to send admin confirmation email: {e}")
    
    return Response({
        'success': True,
        'message': f'Booking {booking_reference} confirmed successfully',
        'booking_status': booking.booking_status,
        'email_sent': email_sent
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_decline_booking(request, booking_reference):
    """
    Admin endpoint to decline/cancel a booking
    """
    # Check if user is admin
    if not request.user.is_staff:
        return Response({
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    booking = get_object_or_404(Booking, booking_reference=booking_reference)
    
    # Check if booking can be declined
    if booking.booking_status in ['cancelled', 'completed']:
        return Response({
            'error': f'Cannot decline booking. Current status: {booking.booking_status}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get decline reason from request
    decline_reason = request.data.get('reason', 'Declined by admin')
    
    # Update booking status
    old_status = booking.booking_status
    booking.booking_status = 'cancelled'
    booking.cancellation_date = timezone.now()
    booking.save()
    
    # Create status history
    BookingStatusHistory.objects.create(
        booking=booking,
        old_status=old_status,
        new_status='cancelled',
        changed_by=request.user,
        reason=f'Declined by admin: {decline_reason}'
    )
    
    # Create cancellation record if it doesn't exist
    if not hasattr(booking, 'cancellation'):
        BookingCancellation.objects.create(
            booking=booking,
            reason='other',
            reason_details=decline_reason,
            cancelled_by=request.user,
            refund_amount=booking.total_amount
        )
    
    # Send decline email
    email_sent = False
    try:
        email_sent = send_admin_decline_email(booking, decline_reason)
    except Exception as e:
        logger.error(f"Failed to send admin decline email: {e}")
    
    return Response({
        'success': True,
        'message': f'Booking {booking_reference} declined successfully',
        'booking_status': booking.booking_status,
        'email_sent': email_sent
    })

def send_admin_confirmation_email(booking):
    """Send booking confirmation email when admin confirms"""
    subject = f'Booking Confirmed - {booking.booking_reference}'
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #28a745;">Your Booking is Confirmed!</h2>
        
        <p>Dear {booking.full_name},</p>
        
        <p>Great news! Your booking has been confirmed by our team.</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>Booking Details:</h3>
            <p><strong>Reference:</strong> {booking.booking_reference}</p>
            <p><strong>Tour:</strong> {booking.tour.title}</p>
            <p><strong>Date:</strong> {booking.preferred_date}</p>
            <p><strong>Time:</strong> {booking.preferred_time or 'To be confirmed'}</p>
            <p><strong>Travelers:</strong> {booking.number_of_travelers}</p>
            <p><strong>Total:</strong> ${booking.total_amount}</p>
        </div>
        
        <p>We will contact you soon with more details about your tour.</p>
        
        <p>Best regards,<br> NATA STORIA TRAVEL Team</p>
    </div>
    """
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=f"Dear {booking.full_name}, your booking {booking.booking_reference} has been confirmed!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    return email.send(fail_silently=False)

def send_admin_decline_email(booking, reason):
    """Send booking decline email when admin declines"""
    subject = f'Booking Update - {booking.booking_reference}'
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc3545;">Booking Update</h2>
        
        <p>Dear {booking.full_name},</p>
        
        <p>We regret to inform you that your booking has been cancelled.</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>Booking Details:</h3>
            <p><strong>Reference:</strong> {booking.booking_reference}</p>
            <p><strong>Tour:</strong> {booking.tour.title}</p>
            <p><strong>Date:</strong> {booking.preferred_date}</p>
            <p><strong>Reason:</strong> {reason}</p>
        </div>
        
        <p>If you have any questions, please contact us.</p>
        
        <p>Best regards,<br> NATA STORIA TRAVEL Team</p>
    </div>
    """
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=f"Dear {booking.full_name}, your booking {booking.booking_reference} has been cancelled.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    return email.send(fail_silently=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_booking_voucher(request, booking_reference):
    """
    Admin endpoint to download voucher for any booking
    """
    # Check if user is admin
    if not request.user.is_staff:
        return Response({
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    booking = get_object_or_404(Booking, booking_reference=booking_reference)
    
    # Use the existing voucher generation code but for admin
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="admin-voucher-{booking.booking_reference}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, " NATA STORIA TRAVEL - ADMIN VOUCHER")
    
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 80, f"Booking: {booking.booking_reference}")

    # Booking details
    p.setFont("Helvetica", 14)
    y_pos = height - 120
    
    details = [
        f"Customer: {booking.full_name}",
        f"Email: {booking.email}",
        f"Phone: {booking.phone}",
        f"Tour: {booking.tour.title}",
        f"Date: {booking.preferred_date}",
        f"Time: {booking.preferred_time or 'TBD'}",
        f"Travelers: {booking.number_of_travelers}",
        f"Status: {booking.booking_status.upper()}",
        f"Total: ${booking.total_amount}",
    ]
    
    for detail in details:
        p.drawString(50, y_pos, detail)
        y_pos -= 25

    # Admin info
    p.setFont("Helvetica", 10)
    p.drawString(50, 50, f"Generated by admin: {request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}")

    p.showPage()
    p.save()
    
    return response