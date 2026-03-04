from django.contrib import admin
from activities.models import (
    HydrationLog, HydrationContent, Medication, MedicationLog,
    NutritionLog, NutritionGoal, FoodSuggestion
)

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


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'dosage', 'frequency_text', 'is_active', 'start_date', 'created_at')
    list_filter = ('is_active', 'frequency_period', 'created_at')
    search_fields = ('user__email', 'user__phone', 'name')
    ordering = ('-created_at',)
    list_editable = ('is_active',)
    readonly_fields = ('frequency_text', 'dose_times')


@admin.register(MedicationLog)
class MedicationLogAdmin(admin.ModelAdmin):
    list_display = ('medication', 'date', 'dose_index', 'dose_time', 'taken', 'taken_at', 'created_at')
    list_filter = ('taken', 'date', 'created_at')
    search_fields = ('medication__name', 'medication__user__email')
    ordering = ('-date', 'dose_index')
    list_editable = ('taken',)


@admin.register(NutritionLog)
class NutritionLogAdmin(admin.ModelAdmin):
    list_display = ('customer', 'date', 'name', 'calories', 'carbs', 'protein', 'fat', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('customer__user__email', 'customer__user__phone', 'name')
    ordering = ('-date', '-created_at')


@admin.register(NutritionGoal)
class NutritionGoalAdmin(admin.ModelAdmin):
    list_display = ('customer', 'calories', 'carbs', 'protein', 'fat', 'created_at', 'updated_at')
    search_fields = ('customer__user__email', 'customer__user__phone')
    ordering = ('-created_at',)


@admin.register(FoodSuggestion)
class FoodSuggestionAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'carbs', 'protein', 'fat', 'usage_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('-usage_count', 'name')
    list_editable = ('is_active',)
