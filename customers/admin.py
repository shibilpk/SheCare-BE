from django.contrib import admin
from .models import Reminder

# Register your models here.


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'customer', 'enabled', 'time', 'days_advance', 'reminder_type')
    list_filter = ('enabled', 'reminder_type')
    search_fields = ('customer__user__email', 'customer__user__first_name')
    readonly_fields = ('get_title', 'get_icon', 'get_color')

    def get_title(self, obj):
        return obj.title
    get_title.short_description = 'Title'

    def get_icon(self, obj):
        return obj.icon
    get_icon.short_description = 'Icon'

    def get_color(self, obj):
        return obj.color
    get_color.short_description = 'Color'

