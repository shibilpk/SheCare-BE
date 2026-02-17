from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import timedelta

from .models import Period, PeriodProfile
from .services import calculate_average_cycle_data


def recalculate_period_profile(customer):
    """
    Recalculate and update period profile based on current periods.
    Used by both post_save and post_delete signals.
    """
    from django.utils.timezone import now

    period_profile, _ = PeriodProfile.objects.get_or_create(customer=customer)

    # Get the most recent period
    latest_period = Period.objects.filter(
        customer=customer
    ).order_by('-start_date').first()

    if not latest_period:
        # No periods left - reset profile to defaults
        period_profile.last_period = None
        period_profile.avg_cycle_length = 28  # Default
        period_profile.avg_period_length = 5  # Default
        period_profile.save(update_fields=[
            "last_period",
            "avg_cycle_length",
            "avg_period_length"
        ])
        return

    # Recalculate averages if using average cycle
    if period_profile.use_average_cycle:
        avg_data = calculate_average_cycle_data(customer)
        if avg_data:
            period_profile.avg_cycle_length = avg_data['avg_cycle_length']
            period_profile.avg_period_length = avg_data['avg_period_length']

    # Get reference period (completed period for calculations)
    today = now()
    reference_period = latest_period

    # If latest period is ongoing, use last completed period for calculations
    # but still keep the latest as the reference
    if latest_period.end_date.date() > today.date():
        last_completed = Period.objects.filter(
            customer=customer,
            end_date__lt=today
        ).order_by('-end_date').first()
        if last_completed:
            reference_period = last_completed

    # Update profile with reference to the period
    # (next_period_start_date will be calculated automatically via property)
    period_profile.last_period = reference_period

    # Calculate and update cycle regularity
    regularity, variance = period_profile.get_cycle_regularity()
    period_profile.cycle_regularity = regularity
    period_profile.cycle_variance = variance

    # Save period profile with updated data
    period_profile.save(update_fields=[
        "last_period",
        "avg_cycle_length",
        "avg_period_length",
        "cycle_regularity",
        "cycle_variance"
    ])


@receiver(post_save, sender=Period)
def update_period_profile_on_save(sender, instance, created, **kwargs):
    """Update period profile after saving a period record"""
    recalculate_period_profile(instance.customer)


@receiver(post_delete, sender=Period)
def update_period_profile_on_delete(sender, instance, **kwargs):
    """Update period profile after deleting a period record"""
    recalculate_period_profile(instance.customer)
