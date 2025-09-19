# tours/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Tour listings
    path('', views.TourListView.as_view(), name='tour_list'),
    path('featured/', views.FeaturedToursView.as_view(), name='featured_tours'),
    path('popular/', views.PopularToursView.as_view(), name='popular_tours'),
    path('categories/', views.TourCategoryListView.as_view(), name='tour_categories'),
    path('stats/', views.tour_stats, name='tour_stats'),
    path('search-suggestions/', views.tour_search_suggestions, name='tour_search_suggestions'),
    
    # Specific tour details
    path('<slug:id>/', views.TourDetailView.as_view(), name='tour_detail'),
    path('<slug:tour_slug>/availability/', views.tour_availability, name='tour_availability'),
    
    # Reviews
    path('<slug:tour_slug>/reviews/', views.TourReviewListView.as_view(), name='tour_reviews'),
    path('<slug:tour_slug>/reviews/create/', views.CreateTourReviewView.as_view(), name='create_tour_review'),
]