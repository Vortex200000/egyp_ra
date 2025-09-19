# tours/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid

from tour_backend import settings

class TourCategory(models.Model):
    """
    Categories for tours (e.g., Adventure, Cultural, Nature, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For icon class names
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tour Categories"

    def __str__(self):
        return self.name

class Tour(models.Model):
    """
    Main tour model
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('hard', 'Hard'),
        ('extreme', 'Extreme'),
    ]

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300)
    
    # Location and Details
    location = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Pricing and Capacity
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # For discounts
    duration = models.CharField(max_length=100)  # e.g., "3 hours", "Full day", "2 days"
    duration_hours = models.IntegerField(default=1)  # For filtering and sorting
    max_persons = models.IntegerField(validators=[MinValueValidator(1)])
    min_persons = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Classification
    category = models.ForeignKey(TourCategory, on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    
    # Media
    cover_photo = models.ImageField(upload_to='tour_images/')
    
    # Features and Inclusions
    includes = models.TextField(help_text="What's included in the tour (one item per line)")
    excludes = models.TextField(blank=True, help_text="What's not included (one item per line)")
    requirements = models.TextField(blank=True, help_text="Requirements for participants")
    
    # Rating and Reviews
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.IntegerField(default=0)
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    available_from = models.DateField(null=True, blank=True)
    available_to = models.DateField(null=True, blank=True)
    
    # SEO and Meta
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['price']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            return round(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    @property
    def is_on_sale(self):
        return self.original_price and self.original_price > self.price

    @property
    def includes_list(self):
        return [item.strip() for item in self.includes.split('\n') if item.strip()]

    @property
    def excludes_list(self):
        return [item.strip() for item in self.excludes.split('\n') if item.strip()]

class TourImage(models.Model):
    """
    Additional images for tours
    """
    tour = models.ForeignKey(Tour, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='tour_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.tour.title} - Image {self.order}"

class TourAvailability(models.Model):
    """
    Specific dates and times when tours are available
    """
    tour = models.ForeignKey(Tour, related_name='availability_slots', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    available_spots = models.IntegerField()
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        # unique_together = ['tour', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.tour.title} ({self.rating} stars) {self.date} {self.start_time}"
    
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.tour.title} - {self.date} at {self.start_time}"

    @property
    def is_available(self):
        return self.is_active and self.available_spots > 0

class TourReview(models.Model):
    """
    Customer reviews for tours
    """
    tour = models.ForeignKey(Tour, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_verified = models.BooleanField(default=False)  # Only for customers who booked
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['tour', 'user']