from django.contrib import admin
from .models import Tour, TourCategory, TourImage, TourAvailability, TourReview

@admin.register(TourCategory)
class TourCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 3

class TourAvailabilityInline(admin.TabularInline):
    model = TourAvailability
    extra = 2

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'price', 'duration', 'max_persons', 'rating', 'is_active', 'is_featured')
    list_filter = ('category', 'difficulty', 'is_active', 'is_featured', 'created_at')
    search_fields = ('title', 'location', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TourImageInline, TourAvailabilityInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'short_description', 'description')
        }),
        ('Location & Details', {
            'fields': ('location', 'address', 'latitude', 'longitude', 'duration', 'duration_hours', 'difficulty')
        }),
        ('Pricing & Capacity', {
            'fields': ('price', 'original_price', 'max_persons', 'min_persons')
        }),
        ('Media', {
            'fields': ('cover_photo',)
        }),
        ('Features', {
            'fields': ('includes', 'excludes', 'requirements')
        }),
        ('Status & Visibility', {
            'fields': ('is_active', 'is_featured', 'available_from', 'available_to')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        })
    )

@admin.register(TourReview)
class TourReviewAdmin(admin.ModelAdmin):
    list_display = ('tour', 'user', 'rating', 'is_verified', 'is_active', 'created_at')
    list_filter = ('rating', 'is_verified', 'is_active', 'created_at')
    search_fields = ('tour__title', 'user__email', 'title', 'comment')
