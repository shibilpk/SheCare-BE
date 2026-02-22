from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.


class HydrationLog(models.Model):
    """Model to track water intake for users"""
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='hydration_logs')
    date = models.DateField(db_index=True)
    amount_ml = models.IntegerField(default=0, help_text="Total water intake in milliliters")
    glass_size_ml = models.IntegerField(default=250, help_text="Default glass size in milliliters")
    daily_goal_ml = models.IntegerField(default=2000, help_text="Daily water intake goal in milliliters")
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

    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
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
