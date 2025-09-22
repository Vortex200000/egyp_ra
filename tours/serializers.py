# tours/serializers.py

from rest_framework import serializers
from .models import Tour, TourCategory, TourImage, TourAvailability, TourReview

class TourCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for tour categories
    """
    class Meta:
        model = TourCategory
        fields = '__all__'

class TourImageSerializer(serializers.ModelSerializer):
    """
    Serializer for tour images
    """
    class Meta:
        model = TourImage
        fields = '__all__'

class TourAvailabilitySerializer(serializers.ModelSerializer):
    """
    Serializer for tour availability slots
    """
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = TourAvailability
        fields = '__all__'

class TourReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for tour reviews
    """
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.ImageField(source='user.profile_picture', read_only=True)
    
    class Meta:
        model = TourReview
        fields = '__all__'
        read_only_fields = ('user', 'is_verified', 'created_at', 'updated_at')

class TourListSerializer(serializers.ModelSerializer):
    """
    Serializer for tour list (minimal data for performance)
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    is_on_sale = serializers.ReadOnlyField()
    
    class Meta:
        model = Tour
        fields = [
            'id', 'title', 'slug', 'short_description', 'location', 'price', 
            'original_price', 'duration', 'max_persons', 'cover_photo', 'rating', 
            'review_count', 'category_name', 'difficulty', 'is_featured', 
            'discount_percentage', 'is_on_sale' 
        ]

class TourDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed tour information
    """
    category = TourCategorySerializer(read_only=True)
    images = TourImageSerializer(many=True, read_only=True)
    availability_slots = TourAvailabilitySerializer(many=True, read_only=True)
    reviews = TourReviewSerializer(many=True, read_only=True)
    
    # Computed fields
    discount_percentage = serializers.ReadOnlyField()
    is_on_sale = serializers.ReadOnlyField()
    includes_list = serializers.ReadOnlyField()
    excludes_list = serializers.ReadOnlyField()
    
    class Meta:
        model = Tour
        fields = '__all__'

class CreateTourReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for creating tour reviews
    """
    class Meta:
        model = TourReview
        fields = ['tour', 'rating', 'title', 'comment']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class TourSearchSerializer(serializers.Serializer):
    """
    Serializer for tour search parameters
    """
    search = serializers.CharField(required=False, help_text="Search in title and description")
    location = serializers.CharField(required=False, help_text="Filter by location")
    category = serializers.UUIDField(required=False, help_text="Filter by category ID")
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    difficulty = serializers.ChoiceField(choices=Tour.DIFFICULTY_CHOICES, required=False)
    min_rating = serializers.DecimalField(max_digits=3, decimal_places=2, required=False)
    max_persons = serializers.IntegerField(required=False, help_text="Minimum capacity needed")
    date_from = serializers.DateField(required=False, help_text="Available from date")
    date_to = serializers.DateField(required=False, help_text="Available to date")
    is_featured = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(
        choices=[
            'title', '-title', 'price', '-price', 'rating', '-rating', 
            'created_at', '-created_at', 'duration_hours', '-duration_hours'
        ],
        required=False,
        default='-is_featured'
    )