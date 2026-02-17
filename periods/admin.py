from django.contrib import admin
from .models import Period, PeriodProfile


@admin.register(PeriodProfile)
class PeriodProfileAdmin(admin.ModelAdmin):
    list_display = ['customer', 'avg_cycle_length', 'avg_period_length', 'cycle_regularity', 'last_period']
    list_filter = ['cycle_regularity', 'use_average_cycle']
    search_fields = ['customer__user__email', 'customer__user__first_name']
    readonly_fields = ['cycle_regularity', 'cycle_variance']


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ['customer', 'start_date', 'end_date', 'period_length', 'cycle_length']
    list_filter = ['start_date']
    search_fields = ['customer__user__email', 'customer__user__first_name']
    readonly_fields = ['period_length', 'cycle_length']
    date_hierarchy = 'start_date'
