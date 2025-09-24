# from django.contrib import admin
# from .models import (
#     Booking, BookingTraveler, BookingStatusHistory, 
#     BookingCancellation, BookingPayment
# )

# class BookingTravelerInline(admin.TabularInline):
#     model = BookingTraveler
#     extra = 1

# class BookingStatusHistoryInline(admin.TabularInline):
#     model = BookingStatusHistory
#     extra = 0
#     readonly_fields = ('created_at',)

# @admin.register(Booking)
# class BookingAdmin(admin.ModelAdmin):
#     list_display = (
#         'booking_reference', 'full_name', 'tour', 'preferred_date', 
#         'number_of_travelers', 'total_amount', 'booking_status', 
#         'payment_status', 'created_at'
#     )
#     list_filter = (
#         'booking_status', 'payment_status', 'preferred_date', 
#         'created_at', 'tour__category'
#     )
#     search_fields = (
#         'booking_reference', 'first_name', 'last_name', 'email', 
#         'tour__title', 'user__email'
#     )
#     readonly_fields = ('booking_reference', 'created_at', 'updated_at', 'booking_date')
#     inlines = [BookingTravelerInline, BookingStatusHistoryInline]
    
#     fieldsets = (
#         ('Booking Information', {
#             'fields': ('booking_reference', 'booking_status', 'payment_status')
#         }),
#         ('Customer Information', {
#             'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
#         }),
#         ('Tour Details', {
#             'fields': (
#                 'tour', 'preferred_date', 'preferred_time', 
#                 'number_of_travelers', 'special_requests'
#             )
#         }),
#         ('Pricing', {
#             'fields': ('tour_price', 'discount_amount', 'tax_amount', 'total_amount')
#         }),
#         ('Payment Information', {
#             'fields': ('payment_intent_id', 'payment_method', 'transaction_id')
#         }),
#         ('Notes', {
#             'fields': ('customer_notes', 'internal_notes')
#         }),
#         ('Important Dates', {
#             'fields': (
#                 'booking_date', 'confirmation_date', 'cancellation_date', 
#                 'completion_date', 'created_at', 'updated_at'
#             )
#         })
#     )

#     actions = ['confirm_bookings', 'cancel_bookings']

#     def confirm_bookings(self, request, queryset):
#         updated = queryset.update(booking_status='confirmed')
#         self.message_user(request, f'{updated} bookings confirmed.')
#     confirm_bookings.short_description = 'Confirm selected bookings'

#     def cancel_bookings(self, request, queryset):
#         updated = queryset.update(booking_status='cancelled')
#         self.message_user(request, f'{updated} bookings cancelled.')
#     cancel_bookings.short_description = 'Cancel selected bookings'

# @admin.register(BookingCancellation)
# class BookingCancellationAdmin(admin.ModelAdmin):
#     list_display = (
#         'booking', 'reason', 'refund_amount', 'refund_processed', 
#         'cancelled_by', 'created_at'
#     )
#     list_filter = ('reason', 'refund_processed', 'created_at')
#     search_fields = ('booking__booking_reference', 'reason_details')


# bookings/admin.py

from django.contrib import admin
from .models import (
    Booking, BookingTraveler, BookingStatusHistory, 
    BookingCancellation, BookingPayment
)

class BookingTravelerInline(admin.TabularInline):
    model = BookingTraveler
    extra = 1

class BookingStatusHistoryInline(admin.TabularInline):
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_reference', 'full_name', 'tour', 'availability_description', 
        'number_of_travelers', 'total_amount', 'booking_status', 
        'payment_status', 'created_at'
    )
    list_filter = (
        'booking_status', 'payment_status', 'availability_description',
        'created_at', 'tour__category'
    )
    search_fields = (
        'booking_reference', 'first_name', 'last_name', 'email', 
        'tour__title', 'user__email', 'availability_description'
    )
    readonly_fields = ('booking_reference', 'created_at', 'updated_at', 'booking_date')
    inlines = [BookingTravelerInline, BookingStatusHistoryInline]
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'booking_status', 'payment_status')
        }),
        ('Customer Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Tour Details', {
            'fields': (
                'tour', 'availability_description', 'preferred_time', 
                'number_of_travelers', 'special_requests'
            )
        }),
        ('Legacy Date (Optional)', {
            'fields': ('preferred_date',),
            'classes': ('collapse',),  # This collapses the section by default
            'description': 'Legacy preferred date field - only visible for existing bookings'
        }),
        ('Pricing', {
            'fields': ('tour_price', 'discount_amount', 'tax_amount', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_intent_id', 'payment_method', 'transaction_id')
        }),
        ('Notes', {
            'fields': ('customer_notes', 'internal_notes')
        }),
        ('Important Dates', {
            'fields': (
                'booking_date', 'confirmation_date', 'cancellation_date', 
                'completion_date', 'created_at', 'updated_at'
            )
        })
    )

    actions = ['confirm_bookings', 'cancel_bookings', 'update_availability_descriptions']

    def confirm_bookings(self, request, queryset):
        updated = queryset.update(booking_status='confirmed')
        self.message_user(request, f'{updated} bookings confirmed.')
    confirm_bookings.short_description = 'Confirm selected bookings'

    def cancel_bookings(self, request, queryset):
        updated = queryset.update(booking_status='cancelled')
        self.message_user(request, f'{updated} bookings cancelled.')
    cancel_bookings.short_description = 'Cancel selected bookings'

    def update_availability_descriptions(self, request, queryset):
        """Bulk update availability descriptions for selected bookings"""
        updated = queryset.update(availability_description='Available all week')
        self.message_user(request, f'{updated} bookings updated with default availability description.')
    update_availability_descriptions.short_description = 'Set availability to "Available all week"'

@admin.register(BookingCancellation)
class BookingCancellationAdmin(admin.ModelAdmin):
    list_display = (
        'booking', 'reason', 'refund_amount', 'refund_processed', 
        'cancelled_by', 'created_at'
    )
    list_filter = ('reason', 'refund_processed', 'created_at')
    search_fields = ('booking__booking_reference', 'reason_details')