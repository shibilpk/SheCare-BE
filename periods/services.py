from django.utils.timezone import now
from django.db.models import Avg
from .models import Period, PeriodProfile
from general.models import AppAdminSettings


def calculate_average_cycle_data(customer):
    """
    Calculate average cycle length and period length for a customer
    based on their historical period data
    """
    # Get the last N periods (configurable, default 3)
    try:
        settings = AppAdminSettings.objects.first()
        periods_to_consider = settings.periods_for_average if settings else 3
    except Exception:
        periods_to_consider = 3

    # Get recent periods with cycle length calculated
    periods = Period.objects.filter(
        customer=customer,
        cycle_length__isnull=False
    ).order_by('-start_date')[:periods_to_consider]

    if not periods.exists():
        return None

    # Calculate averages
    avg_cycle = periods.aggregate(avg=Avg('cycle_length'))['avg']
    avg_period = periods.aggregate(avg=Avg('period_length'))['avg']

    if avg_cycle and avg_period:
        return {
            'avg_cycle_length': round(avg_cycle),
            'avg_period_length': round(avg_period),
        }

    return None


def get_current_period_status(customer):
    """
    Get the current period status for a customer
    """
    profile = PeriodProfile.objects.filter(customer=customer).first()

    if not profile:
        return {
            'has_profile': False,
            'message': 'No period profile found'
        }

    today = now().date()

    # Check if currently in period
    active_period = Period.objects.filter(
        customer=customer,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).first()

    return {
        'has_profile': True,
        'in_period': active_period is not None,
        'is_fertile': profile.is_fertile_today,
        'next_period_date': profile.next_period_start_date,
        'ovulation_date': profile.ovulation_date,
        'fertile_window_start': profile.fertile_window_start,
        'fertile_window_end': profile.fertile_window_end,
        'avg_cycle_length': profile.avg_cycle_length,
        'avg_period_length': profile.avg_period_length,
    }
