from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

from .models import Period, PeriodProfile
from .services import calculate_average_cycle_data


@receiver(post_save, sender=Period)
def update_period_profile(sender, instance, created, **kwargs):
    """Update period profile after saving a period record"""
    period_profile, _ = PeriodProfile.objects.get_or_create(
        customer=instance.customer
    )

    # Update last period end date
    period_profile.last_period_end_date = instance.end_date.date()

    # If user prefers to use average cycle, calculate it
    if period_profile.use_average_cycle:
        avg_data = calculate_average_cycle_data(instance.customer)
        if avg_data:
            period_profile.avg_cycle_length = avg_data['avg_cycle_length']
            period_profile.avg_period_length = avg_data['avg_period_length']

    # Calculate next period start date
    period_profile.next_period_start_date = (
        period_profile.last_period_end_date +
        timedelta(days=period_profile.avg_cycle_length)
    )

    # Save period profile with updated data
    period_profile.save(update_fields=[
        "last_period_end_date",
        "next_period_start_date",
        "avg_cycle_length",
        "avg_period_length"
    ])
