from django.contrib import admin
from .models import (
    AppVersion, AppAdminSettings, DailyTip, BlogPost,
    StaticContent, ContactUs, Feedback, HealthTip
)


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ('version', 'os', 'release_date', 'force_update')
    list_filter = ('os', 'force_update')
    search_fields = ('version',)


@admin.register(AppAdminSettings)
class AppAdminSettingsAdmin(admin.ModelAdmin):
    list_display = ('no_avg_period_months',)


@admin.register(DailyTip)
class DailyTipAdmin(admin.ModelAdmin):
    list_display = ('date', 'language', 'created_at')
    list_filter = ('language',)
    search_fields = ('short_description',)
    date_hierarchy = 'date'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_date', 'created_at')
    list_filter = ('published_date',)
    search_fields = ('title', 'author')
    date_hierarchy = 'published_date'


@admin.register(StaticContent)
class StaticContentAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'created_at', 'updated_at')
    list_filter = ('content_type',)


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message Details', {
            'fields': ('subject', 'message')
        }),
        ('Admin Section', {
            'fields': ('is_resolved', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'feedback_type', 'rating', 'is_reviewed', 'created_at')
    list_filter = ('feedback_type', 'rating', 'is_reviewed', 'created_at')
    search_fields = ('name', 'email', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('name', 'email')
        }),
        ('Feedback Details', {
            'fields': ('feedback_type', 'rating', 'message')
        }),
        ('Admin Section', {
            'fields': ('is_reviewed', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(HealthTip)
class HealthTipAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'order', 'is_active')
    list_filter = ('is_active', 'category')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description')
