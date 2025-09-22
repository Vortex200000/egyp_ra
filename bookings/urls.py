# bookings/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Booking creation and management
    path('create/', views.CreateBookingView.as_view(), name='create_booking'),
    
    # User bookings (authenticated users)
    path('my-bookings/', views.UserBookingListView.as_view(), name='user_bookings'),
    path('my-bookings/<str:booking_reference>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('my-bookings/<str:booking_reference>/update/', views.UpdateBookingView.as_view(), name='update_booking'),
    path('my-bookings/<str:booking_reference>/cancel/', views.CancelBookingView.as_view(), name='cancel_booking'),
    path('<str:booking_reference>/voucher/', views.booking_voucher, name='booking_voucher'),
    
    # Guest booking lookup and management
    path('lookup/', views.guest_booking_lookup, name='guest_booking_lookup'),
    path('cancel-guest/', views.cancel_guest_booking, name='cancel_guest_booking'),
    
    # User statistics and quick access
    path('stats/', views.user_booking_stats, name='user_booking_stats'),
    path('upcoming/', views.upcoming_bookings, name='upcoming_bookings'),

      path('admin/all/', views.admin_all_bookings, name='admin_all_bookings'),
    path('admin/<str:booking_reference>/confirm/', views.admin_confirm_booking, name='admin_confirm_booking'),
    path('admin/<str:booking_reference>/decline/', views.admin_decline_booking, name='admin_decline_booking'),
    path('admin/<str:booking_reference>/voucher/', views.admin_booking_voucher, name='admin_booking_voucher'),

]