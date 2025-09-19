# tours/views.py

from rest_framework import generics, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from .models import Tour, TourCategory, TourReview, TourAvailability
from .serializers import (
    TourListSerializer, 
    TourDetailSerializer, 
    TourCategorySerializer,
    CreateTourReviewSerializer,
    TourReviewSerializer,
    TourAvailabilitySerializer
)

class TourListView(generics.ListAPIView):
    """
    List all active tours with filtering and search
    """
    serializer_class = TourListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty', 'location', 'is_featured']
    search_fields = ['title', 'description', 'location', 'short_description']
    ordering_fields = ['title', 'price', 'rating', 'created_at', 'duration_hours']
    ordering = ['-is_featured', '-created_at']

    def get_queryset(self):
        queryset = Tour.objects.filter(is_active=True).select_related('category')
        
        # Custom filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        min_rating = self.request.query_params.get('min_rating')
        max_persons = self.request.query_params.get('max_persons')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        if max_persons:
            queryset = queryset.filter(max_persons__gte=max_persons)
            
        return queryset

class TourDetailView(generics.RetrieveAPIView):
    """
    Get detailed information about a specific tour
    """
    serializer_class = TourDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        return Tour.objects.filter(is_active=True).select_related('category').prefetch_related(
            'images', 
            'availability_slots',
            'reviews__user'
        )

class FeaturedToursView(generics.ListAPIView):
    """
    Get featured tours
    """
    serializer_class = TourListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Tour.objects.filter(is_active=True, is_featured=True).select_related('category')[:6]

class PopularToursView(generics.ListAPIView):
    """
    Get popular tours based on ratings and bookings
    """
    serializer_class = TourListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Tour.objects.filter(
            is_active=True, 
            rating__gte=4.0, 
            review_count__gte=5
        ).select_related('category').order_by('-rating', '-review_count')[:6]

class TourCategoryListView(generics.ListAPIView):
    """
    List all tour categories
    """
    serializer_class = TourCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = TourCategory.objects.filter(is_active=True)

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def tour_availability(request, tour_slug):
    """
    Get availability for a specific tour
    """
    tour = get_object_or_404(Tour, slug=tour_slug, is_active=True)
    
    # Get query parameters for date filtering
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    availability = TourAvailability.objects.filter(tour=tour, is_active=True)
    
    if date_from:
        availability = availability.filter(date__gte=date_from)
    if date_to:
        availability = availability.filter(date__lte=date_to)
        
    serializer = TourAvailabilitySerializer(availability, many=True)
    
    return Response({
        'success': True,
        'tour': tour.title,
        'availability': serializer.data
    })

class TourReviewListView(generics.ListAPIView):
    """
    List reviews for a specific tour
    """
    serializer_class = TourReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        tour_slug = self.kwargs['tour_slug']
        tour = get_object_or_404(Tour, slug=tour_slug)
        return TourReview.objects.filter(tour=tour, is_active=True).select_related('user').order_by('-created_at')

class CreateTourReviewView(generics.CreateAPIView):
    """
    Create a review for a tour
    """
    serializer_class = CreateTourReviewSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        tour_slug = kwargs.get('tour_slug')
        tour = get_object_or_404(Tour, slug=tour_slug)
        
        # Check if user already reviewed this tour
        if TourReview.objects.filter(tour=tour, user=request.user).exists():
            return Response({
                'success': False,
                'message': 'You have already reviewed this tour'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add tour to the data
        mutable_data = request.data.copy()
        mutable_data['tour'] = tour.id
        
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        
        # Update tour's average rating
        self.update_tour_rating(tour)
        
        return Response({
            'success': True,
            'message': 'Review created successfully',
            'review': TourReviewSerializer(review).data
        }, status=status.HTTP_201_CREATED)

    def update_tour_rating(self, tour):
        """Update tour's average rating and review count"""
        reviews = TourReview.objects.filter(tour=tour, is_active=True)
        if reviews.exists():
            tour.rating = reviews.aggregate(Avg('rating'))['rating__avg']
            tour.review_count = reviews.count()
            tour.save(update_fields=['rating', 'review_count'])

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def tour_search_suggestions(request):
    """
    Get search suggestions based on query
    """
    query = request.query_params.get('q', '')
    
    if len(query) < 2:
        return Response({
            'success': True,
            'suggestions': []
        })
    
    # Search in tour titles and locations
    tours = Tour.objects.filter(
        Q(title__icontains=query) | Q(location__icontains=query),
        is_active=True
    ).values('title', 'slug', 'location').distinct()[:10]
    
    suggestions = []
    for tour in tours:
        suggestions.append({
            'title': tour['title'],
            'slug': tour['slug'],
            'location': tour['location'],
            'type': 'tour'
        })
    
    # Add unique locations
    locations = Tour.objects.filter(
        location__icontains=query,
        is_active=True
    ).values_list('location', flat=True).distinct()[:5]
    
    for location in locations:
        if not any(s['location'] == location for s in suggestions):
            suggestions.append({
                'title': location,
                'location': location,
                'type': 'location'
            })
    
    return Response({
        'success': True,
        'suggestions': suggestions
    })

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def tour_stats(request):
    """
    Get overall tour statistics
    """
    stats = {
        'total_tours': Tour.objects.filter(is_active=True).count(),
        'total_categories': TourCategory.objects.filter(is_active=True).count(),
        'average_rating': Tour.objects.filter(is_active=True).aggregate(Avg('rating'))['rating__avg'] or 0,
        'total_reviews': TourReview.objects.filter(is_active=True).count(),
        'featured_tours': Tour.objects.filter(is_active=True, is_featured=True).count(),
    }
    
    # Popular locations (top 5)
    popular_locations = Tour.objects.filter(is_active=True).values('location').annotate(
        tour_count=Count('id')
    ).order_by('-tour_count')[:5]
    
    # Price ranges
    price_stats = Tour.objects.filter(is_active=True).aggregate(
        min_price=models.Min('price'),
        max_price=models.Max('price'),
        avg_price=Avg('price')
    )
    
    return Response({
        'success': True,
        'stats': stats,
        'popular_locations': list(popular_locations),
        'price_stats': price_stats
    })