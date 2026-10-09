from django.contrib import admin
from .models import Pregnancy


@admin.register(Pregnancy)
class PregnancyAdmin(admin.ModelAdmin):
    list_display = ['customer', 'due_date', 'is_active', 'baby_born', 'pregnancy_lost', 'created_at']
    list_filter = ['is_active', 'baby_born', 'pregnancy_lost', 'created_at']
    search_fields = ['customer__user__email', 'baby_name', 'doctor_name']
    readonly_fields = ['created_at', 'updated_at']

