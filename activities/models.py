from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.


class HydrationLog(models.Model):
    """Model to track water intake for users"""
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='hydration_logs')
    date = models.DateField(db_index=True)
    amount_ml = models.IntegerField(
        default=0, help_text="Total water intake in milliliters")
    glass_size_ml = models.IntegerField(
        default=250, help_text="Default glass size in milliliters")
    daily_goal_ml = models.IntegerField(
        default=2000, help_text="Daily water intake goal in milliliters")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.user} - {self.date} - {self.amount_ml}ml"

    @property
    def glasses_count(self):
        """Calculate number of glasses based on amount and glass size"""
        if self.glass_size_ml == 0:
            return 0
        return round(self.amount_ml / self.glass_size_ml, 1)

    @property
    def total_liters(self):
        """Calculate total intake in liters"""
        return round(self.amount_ml / 1000, 2)

    @property
    def progress_percent(self):
        """Calculate progress towards daily goal"""
        if self.daily_goal_ml == 0:
            return 0
        return min(round((self.amount_ml / self.daily_goal_ml) * 100, 2), 100)


class HydrationContent(models.Model):
    """Model to store hydration benefits and tips"""
    CONTENT_TYPE_CHOICES = [
        ('benefit', 'Benefit'),
        ('tip', 'Tip'),
    ]

    content_type = models.CharField(
        max_length=10, choices=CONTENT_TYPE_CHOICES)
    icon = models.CharField(max_length=10, help_text="Emoji icon")
    text = models.TextField(help_text="Benefit or tip text")
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['content_type', 'order']
        indexes = [
            models.Index(fields=['content_type', 'is_active', 'order']),
        ]

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.text[:50]}"


class Medication(models.Model):
    """Model to store user medications"""
    FREQUENCY_PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('once', 'One Time Only'),
    ]

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=200, help_text="Medication name")
    dosage = models.CharField(
        max_length=100, help_text="Dosage (e.g., 1 tablet, 400mcg)")
    frequency_period = models.CharField(
        max_length=10, choices=FREQUENCY_PERIOD_CHOICES, default='daily')
    times_per_period = models.IntegerField(
        default=1, help_text="How many times per period")
    color = models.CharField(
        max_length=7, default='#EC4899', help_text="Hex color code")
    is_active = models.BooleanField(
        default=True, help_text="Is medication currently active")
    start_date = models.DateField(
        null=True, blank=True, help_text="When medication started")
    end_date = models.DateField(
        null=True, blank=True, help_text="When medication ended")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user} - {self.name} ({self.dosage})"

    @property
    def frequency_text(self):
        """Generate human-readable frequency text"""
        if self.frequency_period == 'once':
            return 'One time only'

        times_text = {
            1: 'Once',
            2: 'Twice',
        }.get(self.times_per_period, f"{self.times_per_period} times")

        return f"{times_text} {self.frequency_period}"

    @property
    def dose_times(self):
        """Generate default time labels based on times_per_period"""
        if self.times_per_period == 1:
            return ['Morning']
        elif self.times_per_period == 2:
            return ['Morning', 'Evening']
        elif self.times_per_period == 3:
            return ['Morning', 'Afternoon', 'Evening']
        else:
            return [f"Dose {i+1}" for i in range(self.times_per_period)]


class MedicationLog(models.Model):
    """Model to track medication doses taken"""
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField(db_index=True)
    dose_index = models.IntegerField(
        help_text="Which dose of the day (0-based index)")
    dose_time = models.CharField(
        max_length=50, help_text="Time label (e.g., Morning, Afternoon)")
    taken = models.BooleanField(
        default=False, help_text="Whether dose was taken")
    taken_at = models.DateTimeField(
        null=True, blank=True, help_text="When dose was marked as taken")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('medication', 'date', 'dose_index')
        ordering = ['date', 'dose_index']
        indexes = [
            models.Index(fields=['medication', 'date']),
            models.Index(fields=['date', 'taken']),
        ]

    def __str__(self):
        return f"{self.medication.name} - {self.date} - {self.dose_time} - {'Taken' if self.taken else 'Not Taken'}"


class NutritionLog(models.Model):
    """Model to track daily nutrition/meals"""
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.CASCADE, related_name='nutrition_logs')
    date = models.DateField(db_index=True)
    name = models.CharField(max_length=200, help_text="Meal/food name")
    quantity = models.IntegerField(default=100, help_text="Quantity in grams")
    calories = models.IntegerField(default=0, help_text="Total calories")
    carbs = models.FloatField(default=0, help_text="Carbohydrates in grams")
    protein = models.FloatField(default=0, help_text="Protein in grams")
    fat = models.FloatField(default=0, help_text="Fat in grams")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=['customer', 'date']),
        ]

    def __str__(self):
        return f"{self.customer} - {self.date} - {self.name} ({self.calories} cal)"


class NutritionGoal(models.Model):
    """Model to store customer's daily nutrition goals"""
    customer = models.OneToOneField(
        'customers.Customer', on_delete=models.CASCADE, related_name='nutrition_goal')
    calories = models.IntegerField(default=2000, help_text="Daily calorie goal")
    carbs = models.FloatField(default=250, help_text="Daily carbs goal in grams")
    protein = models.FloatField(default=75, help_text="Daily protein goal in grams")
    fat = models.FloatField(default=70, help_text="Daily fat goal in grams")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nutrition Goal"
        verbose_name_plural = "Nutrition Goals"

    def __str__(self):
        return f"{self.customer} - {self.calories} cal goal"


class FoodSuggestion(models.Model):
    """Model to store common food items for autocomplete"""
    name = models.CharField(max_length=200, unique=True, help_text="Food/meal name")
    calories = models.IntegerField(help_text="Typical calories")
    carbs = models.FloatField(help_text="Typical carbs in grams")
    protein = models.FloatField(help_text="Typical protein in grams")
    fat = models.FloatField(help_text="Typical fat in grams")
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0, help_text="How many times suggested")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-usage_count", "name"]
        indexes = [
            models.Index(fields=['is_active', '-usage_count']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.calories} cal)"
