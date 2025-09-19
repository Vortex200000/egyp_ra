# bookings/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from tours.models import Tour
import uuid
import string
import random

User = get_user_model()

def generate_booking_reference():
    """Generate a unique booking reference"""
    letters = string.ascii_uppercase
    numbers = string.digits
    return ''.join(random.choices(letters, k=3)) + ''.join(random.choices(numbers, k=6))

class Booking(models.Model):
    """
    Main booking model
    """
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    # Primary identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(
        max_length=20, 
        unique=True, 
        default=generate_booking_reference
    )

    # Customer information (for guest bookings)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    # Tour details
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='bookings')
    number_of_travelers = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    preferred_date = models.DateField()
    preferred_time = models.TimeField(null=True, blank=True)
    special_requests = models.TextField(blank=True)

    # Pricing information
    tour_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at booking time
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status tracking
    booking_status = models.CharField(
        max_length=20, 
        choices=BOOKING_STATUS_CHOICES, 
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending'
    )

    # User association (optional for guest bookings)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='bookings'
    )

    # Payment tracking
    payment_intent_id = models.CharField(max_length=200, blank=True)  # Stripe payment intent
    payment_method = models.CharField(max_length=50, default='card')
    transaction_id = models.CharField(max_length=200, blank=True)

    # Internal notes and communication
    internal_notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)

    # Important dates
    booking_date = models.DateTimeField(auto_now_add=True)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['email']),
            models.Index(fields=['user']),
            models.Index(fields=['booking_status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['preferred_date']),
        ]

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.full_name} - {self.tour.title}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_paid(self):
        return self.payment_status == 'paid'

    @property
    def is_confirmed(self):
        return self.booking_status == 'confirmed'

    @property
    def can_be_cancelled(self):
        # Can be cancelled if not completed and tour date is in the future
        return (
            self.booking_status in ['pending', 'confirmed'] and 
            self.preferred_date > timezone.now().date()
        )

    @property
    def days_until_tour(self):
        if self.preferred_date:
            return (self.preferred_date - timezone.now().date()).days
        return None

    def save(self, *args, **kwargs):
        # Calculate total amount if not set
        if not self.total_amount:
            self.total_amount = (self.tour_price * self.number_of_travelers) - self.discount_amount + self.tax_amount
        
        super().save(*args, **kwargs)

class BookingTraveler(models.Model):
    """
    Individual traveler information for bookings
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='travelers')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    dietary_restrictions = models.CharField(max_length=200, blank=True)
    mobility_requirements = models.CharField(max_length=200, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.booking.booking_reference}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class BookingStatusHistory(models.Model):
    """
    Track status changes for bookings
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Booking Status Histories"

    def __str__(self):
        return f"{self.booking.booking_reference}: {self.old_status} → {self.new_status}"

class BookingCancellation(models.Model):
    """
    Track booking cancellations and refund information
    """
    CANCELLATION_REASON_CHOICES = [
        ('customer_request', 'Customer Request'),
        ('tour_cancelled', 'Tour Cancelled'),
        ('weather', 'Weather Conditions'),
        ('insufficient_participants', 'Insufficient Participants'),
        ('force_majeure', 'Force Majeure'),
        ('other', 'Other'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='cancellation')
    reason = models.CharField(max_length=30, choices=CANCELLATION_REASON_CHOICES)
    reason_details = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Refund information
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_processed = models.BooleanField(default=False)
    refund_reference = models.CharField(max_length=100, blank=True)
    refund_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cancellation for {self.booking.booking_reference}"

class BookingPayment(models.Model):
    """
    Track payment transactions for bookings
    """
    PAYMENT_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('partial_refund', 'Partial Refund'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Payment gateway information
    gateway = models.CharField(max_length=50, default='stripe')
    gateway_transaction_id = models.CharField(max_length=200)
    gateway_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payment_type.title()} - {self.booking.booking_reference} - ${self.amount}"