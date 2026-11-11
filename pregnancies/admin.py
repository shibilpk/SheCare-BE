from django.contrib import admin
from .models import Appointment, ChecklistItem, ChildWeightEntry, Pregnancy


@admin.register(Pregnancy)
class PregnancyAdmin(admin.ModelAdmin):
    list_display = ['customer', 'due_date', 'is_active', 'baby_born', 'pregnancy_lost', 'created_at']
    list_filter = ['is_active', 'baby_born', 'pregnancy_lost', 'created_at']
    search_fields = ['customer__user__email', 'baby_name', 'doctor_name']
    readonly_fields = ['created_at', 'updated_at']



@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'title', 'date', 'time', 'doctor', 'is_completed']
    list_filter = ['is_completed', 'date']
    search_fields = ['customer__user__email', 'title', 'doctor']


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['customer', 'category', 'label', 'checked', 'is_custom']
    list_filter = ['category', 'checked', 'is_custom']
    search_fields = ['customer__user__email', 'label']


@admin.register(ChildWeightEntry)
class ChildWeightEntryAdmin(admin.ModelAdmin):
    list_display = ['customer', 'entry_date', 'age_months', 'weight_kg']
    search_fields = ['customer__user__email']
