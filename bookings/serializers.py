# # bookings/serializers.py

# from rest_framework import serializers
# from django.contrib.auth import get_user_model
# from .models import Booking, BookingTraveler, BookingStatusHistory, BookingCancellation, BookingPayment
# from tours.models import Tour

# User = get_user_model()

# class BookingTravelerSerializer(serializers.ModelSerializer):
#     """
#     Serializer for individual traveler information
#     """
#     full_name = serializers.ReadOnlyField()

#     class Meta:
#         model = BookingTraveler
#         fields = '__all__'
#         read_only_fields = ('booking',)

# class BookingStatusHistorySerializer(serializers.ModelSerializer):
#     """
#     Serializer for booking status history
#     """
#     changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

#     class Meta:
#         model = BookingStatusHistory
#         fields = '__all__'

# class BookingPaymentSerializer(serializers.ModelSerializer):
#     """
#     Serializer for booking payments
#     """
#     class Meta:
#         model = BookingPayment
#         fields = '__all__'

# class BookingCancellationSerializer(serializers.ModelSerializer):
#     """
#     Serializer for booking cancellations
#     """
#     cancelled_by_name = serializers.CharField(source='cancelled_by.full_name', read_only=True)
#     reason_display = serializers.CharField(source='get_reason_display', read_only=True)

#     class Meta:
#         model = BookingCancellation
#         fields = '__all__'

# class BookingListSerializer(serializers.ModelSerializer):
#     """
#     Serializer for booking list (minimal information)
#     """
#     tour_title = serializers.CharField(source='tour.title', read_only=True)
#     tour_cover_photo = serializers.ImageField(source='tour.cover_photo', read_only=True)
#     tour_location = serializers.CharField(source='tour.location', read_only=True)
#     full_name = serializers.ReadOnlyField()
#     booking_status_display = serializers.CharField(source='get_booking_status_display', read_only=True)
#     payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
#     days_until_tour = serializers.ReadOnlyField()
#     can_be_cancelled = serializers.ReadOnlyField()

#     class Meta:
#         model = Booking
#         fields = [
#             'id', 'booking_reference', 'full_name', 'tour_title', 'tour_cover_photo',
#             'tour_location', 'preferred_date', 'preferred_time', 'number_of_travelers',
#             'total_amount', 'booking_status', 'booking_status_display', 'payment_status',
#             'payment_status_display', 'days_until_tour', 'can_be_cancelled', 'created_at'
#         ]

# class BookingDetailSerializer(serializers.ModelSerializer):
#     """
#     Serializer for detailed booking information
#     """
#     tour_title = serializers.CharField(source='tour.title', read_only=True)
#     # tour_slug = serializers.CharField(source='tour.slug', read_only=True)
#     tour_cover_photo = serializers.ImageField(source='tour.cover_photo', read_only=True)
#     tour_location = serializers.CharField(source='tour.location', read_only=True)
#     tour_duration = serializers.CharField(source='tour.duration', read_only=True)
#     tour_id = serializers.CharField(source='tour.id', write_only=True)
#     # Computed fields
#     full_name = serializers.ReadOnlyField()
#     booking_status_display = serializers.CharField(source='get_booking_status_display', read_only=True)
#     payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
#     days_until_tour = serializers.ReadOnlyField()
#     can_be_cancelled = serializers.ReadOnlyField()
#     is_paid = serializers.ReadOnlyField()
#     is_confirmed = serializers.ReadOnlyField()
    
#     # Related data
#     travelers = BookingTravelerSerializer(many=True, read_only=True)
#     status_history = BookingStatusHistorySerializer(many=True, read_only=True)
#     payments = BookingPaymentSerializer(many=True, read_only=True)
#     cancellation = BookingCancellationSerializer(read_only=True)

#     class Meta:
#         model = Booking
#         fields = '__all__'

# class CreateBookingSerializer(serializers.ModelSerializer):
#     """
#     Serializer for creating new bookings
#     """
#     travelers = BookingTravelerSerializer(many=True, required=False)
#     tour_id = serializers.CharField(write_only=True)  # Changed from tour_slug to tour_id

#     class Meta:
#         model = Booking
#         fields = [
#             'tour_id', 'first_name', 'last_name', 'email', 'phone',  # Added tour_id back to fields
#             'number_of_travelers', 'preferred_date', 'preferred_time',
#             'special_requests', 'travelers'
#         ]

#     def validate_tour_id(self, value):  # Changed method name from validate_tour_slug
#         try:
#             tour = Tour.objects.get(id=value, is_active=True)
#             return value  # Return the ID, not the Tour object
#         except Tour.DoesNotExist:
#             raise serializers.ValidationError("Invalid tour selected.")

#     def validate_number_of_travelers(self, value):
#         if value < 1:
#             raise serializers.ValidationError("Number of travelers must be at least 1.")
#         return value

#     def validate(self, attrs):
#         tour_id = attrs.get('tour_id')
#         number_of_travelers = attrs.get('number_of_travelers')
        
#         # Get the tour object for validation
#         if tour_id:
#             try:
#                 tour = Tour.objects.get(id=tour_id, is_active=True)
#                 # Check if tour can accommodate the number of travelers
#                 if number_of_travelers > tour.max_persons:
#                     raise serializers.ValidationError(
#                         f"This tour can accommodate maximum {tour.max_persons} persons."
#                     )
                
#                 # Check if number of travelers meets minimum requirement
#                 if number_of_travelers < tour.min_persons:
#                     raise serializers.ValidationError(
#                         f"This tour requires minimum {tour.min_persons} persons."
#                     )
#             except Tour.DoesNotExist:
#                 raise serializers.ValidationError("Invalid tour selected.")
        
#         return attrs

#     def create(self, validated_data):
#         travelers_data = validated_data.pop('travelers', [])
#         tour_id = validated_data.pop('tour_id')  # Get the tour ID
        
#         # Get the tour object
#         tour = Tour.objects.get(id=tour_id)  # We know it exists from validation
        
#         # Set tour-related fields
#         validated_data['tour'] = tour
#         validated_data['tour_price'] = tour.price
#         validated_data['total_amount'] = tour.price * validated_data['number_of_travelers']
        
#         # Associate with user if authenticated
#         request = self.context.get('request')
#         if request and request.user.is_authenticated:
#             validated_data['user'] = request.user

#         # Create booking
#         booking = Booking.objects.create(**validated_data)
        
#         # Create travelers if provided
#         for traveler_data in travelers_data:
#             BookingTraveler.objects.create(booking=booking, **traveler_data)
        
#         # Create initial status history
#         BookingStatusHistory.objects.create(
#             booking=booking,
#             new_status='pending',
#             reason='Booking created'
#         )
        
#         return booking

# class UpdateBookingSerializer(serializers.ModelSerializer):
#     """
#     Serializer for updating booking information (limited fields)
#     """
#     class Meta:
#         model = Booking
#         fields = [
#             'first_name', 'last_name', 'email', 'phone', 'preferred_date',
#             'preferred_time', 'special_requests'
#         ]

#     def validate_preferred_date(self, value):
#         from django.utils import timezone
#         if value <= timezone.now().date():
#             raise serializers.ValidationError("Preferred date must be in the future.")
#         return value

# class CancelBookingSerializer(serializers.Serializer):
#     """
#     Serializer for booking cancellation
#     """
#     reason = serializers.ChoiceField(choices=BookingCancellation.CANCELLATION_REASON_CHOICES)
#     reason_details = serializers.CharField(required=False, allow_blank=True)

# class GuestBookingLookupSerializer(serializers.Serializer):
#     """
#     Serializer for guest booking lookup
#     """
#     booking_reference = serializers.CharField(max_length=20)
#     email = serializers.EmailField()

#     def validate(self, attrs):
#         booking_reference = attrs.get('booking_reference')
#         email = attrs.get('email')
        
#         try:
#             booking = Booking.objects.get(
#                 booking_reference=booking_reference,
#                 email=email
#             )
#             attrs['booking'] = booking
#         except Booking.DoesNotExist:
#             raise serializers.ValidationError(
#                 "No booking found with the provided reference and email."
#             )
        
#         return attrs

# bookings/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Booking, BookingTraveler, BookingStatusHistory, BookingCancellation, BookingPayment
from tours.models import Tour

User = get_user_model()

class BookingTravelerSerializer(serializers.ModelSerializer):
    """
    Serializer for individual traveler information
    """
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = BookingTraveler
        fields = '__all__'
        read_only_fields = ('booking',)

class BookingStatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for booking status history
    """
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model = BookingStatusHistory
        fields = '__all__'

class BookingPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for booking payments
    """
    class Meta:
        model = BookingPayment
        fields = '__all__'

class BookingCancellationSerializer(serializers.ModelSerializer):
    """
    Serializer for booking cancellations
    """
    cancelled_by_name = serializers.CharField(source='cancelled_by.full_name', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)

    class Meta:
        model = BookingCancellation
        fields = '__all__'

class BookingListSerializer(serializers.ModelSerializer):
    """
    Serializer for booking list (minimal information)
    """
    tour_title = serializers.CharField(source='tour.title', read_only=True)
    tour_cover_photo = serializers.ImageField(source='tour.cover_photo', read_only=True)
    tour_location = serializers.CharField(source='tour.location', read_only=True)
    full_name = serializers.ReadOnlyField()
    booking_status_display = serializers.CharField(source='get_booking_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    days_until_tour = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'full_name', 'tour_title', 'tour_cover_photo',
            'tour_location', 'availability_description', 'preferred_time', 'number_of_travelers',
            'total_amount', 'booking_status', 'booking_status_display', 'payment_status',
            'payment_status_display', 'days_until_tour', 'can_be_cancelled', 'created_at',
            # Keep preferred_date for backward compatibility but make it optional
            'preferred_date'
        ]

class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed booking information
    """
    tour_title = serializers.CharField(source='tour.title', read_only=True)
    tour_cover_photo = serializers.ImageField(source='tour.cover_photo', read_only=True)
    tour_location = serializers.CharField(source='tour.location', read_only=True)
    tour_duration = serializers.CharField(source='tour.duration', read_only=True)
    tour_id = serializers.CharField(source='tour.id', write_only=True)
    
    # Computed fields
    full_name = serializers.ReadOnlyField()
    booking_status_display = serializers.CharField(source='get_booking_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    days_until_tour = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    is_paid = serializers.ReadOnlyField()
    is_confirmed = serializers.ReadOnlyField()
    
    # Related data
    travelers = BookingTravelerSerializer(many=True, read_only=True)
    status_history = BookingStatusHistorySerializer(many=True, read_only=True)
    payments = BookingPaymentSerializer(many=True, read_only=True)
    cancellation = BookingCancellationSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

class CreateBookingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new bookings
    """
    travelers = BookingTravelerSerializer(many=True, required=False)
    tour_id = serializers.CharField(write_only=True)

    class Meta:
        model = Booking
        fields = [
            'tour_id', 'first_name', 'last_name', 'email', 'phone',
            'number_of_travelers', 'availability_description', 'preferred_time',
            'special_requests', 'travelers',
            # Keep preferred_date optional for backward compatibility
            'preferred_date'
        ]

    def validate_tour_id(self, value):
        try:
            tour = Tour.objects.get(id=value, is_active=True)
            return value
        except Tour.DoesNotExist:
            raise serializers.ValidationError("Invalid tour selected.")

    def validate_number_of_travelers(self, value):
        if value < 1:
            raise serializers.ValidationError("Number of travelers must be at least 1.")
        return value

    def validate(self, attrs):
        tour_id = attrs.get('tour_id')
        number_of_travelers = attrs.get('number_of_travelers')
        
        # Get the tour object for validation
        if tour_id:
            try:
                tour = Tour.objects.get(id=tour_id, is_active=True)
                # Check if tour can accommodate the number of travelers
                if number_of_travelers > tour.max_persons:
                    raise serializers.ValidationError(
                        f"This tour can accommodate maximum {tour.max_persons} persons."
                    )
                
                # Check if number of travelers meets minimum requirement
                if number_of_travelers < tour.min_persons:
                    raise serializers.ValidationError(
                        f"This tour requires minimum {tour.min_persons} persons."
                    )
            except Tour.DoesNotExist:
                raise serializers.ValidationError("Invalid tour selected.")
        
        return attrs

    def create(self, validated_data):
        travelers_data = validated_data.pop('travelers', [])
        tour_id = validated_data.pop('tour_id')
        
        # Get the tour object
        tour = Tour.objects.get(id=tour_id)
        
        # Set tour-related fields
        validated_data['tour'] = tour
        validated_data['tour_price'] = tour.price
        validated_data['total_amount'] = tour.price * validated_data['number_of_travelers']
        
        # Set default availability description if not provided
        if not validated_data.get('availability_description'):
            validated_data['availability_description'] = 'Available all week'
        
        # Associate with user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user

        # Create booking
        booking = Booking.objects.create(**validated_data)
        
        # Create travelers if provided
        for traveler_data in travelers_data:
            BookingTraveler.objects.create(booking=booking, **traveler_data)
        
        # Create initial status history
        BookingStatusHistory.objects.create(
            booking=booking,
            new_status='pending',
            reason='Booking created'
        )
        
        return booking

class UpdateBookingSerializer(serializers.ModelSerializer):
    """
    Serializer for updating booking information (limited fields)
    """
    class Meta:
        model = Booking
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'availability_description',
            'preferred_time', 'special_requests',
            # Keep preferred_date optional for backward compatibility
            'preferred_date'
        ]

    def validate_preferred_date(self, value):
        # Only validate if preferred_date is provided
        if value:
            from django.utils import timezone
            if value <= timezone.now().date():
                raise serializers.ValidationError("Preferred date must be in the future.")
        return value

class CancelBookingSerializer(serializers.Serializer):
    """
    Serializer for booking cancellation
    """
    reason = serializers.ChoiceField(choices=BookingCancellation.CANCELLATION_REASON_CHOICES)
    reason_details = serializers.CharField(required=False, allow_blank=True)

class GuestBookingLookupSerializer(serializers.Serializer):
    """
    Serializer for guest booking lookup
    """
    booking_reference = serializers.CharField(max_length=20)
    email = serializers.EmailField()

    def validate(self, attrs):
        booking_reference = attrs.get('booking_reference')
        email = attrs.get('email')
        
        try:
            booking = Booking.objects.get(
                booking_reference=booking_reference,
                email=email
            )
            attrs['booking'] = booking
        except Booking.DoesNotExist:
            raise serializers.ValidationError(
                "No booking found with the provided reference and email."
            )
        
        return attrs