from django.contrib import admin
from activities.models import HydrationLog, HydrationContent

# Register your models here.


@admin.register(HydrationLog)
class HydrationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'amount_ml', 'glasses_count', 'progress_percent', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('user__email', 'user__phone')
    ordering = ('-date',)


@admin.register(HydrationContent)
class HydrationContentAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'icon', 'text', 'order', 'is_active', 'created_at')
    list_filter = ('content_type', 'is_active')
    search_fields = ('text',)
    ordering = ('content_type', 'order')
    list_editable = ('order', 'is_active')

