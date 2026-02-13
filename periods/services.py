from django.utils.timezone import now
from django.db.models import Avg
from .models import Period
from general.models import AppAdminSettings


def calculate_main_card_display(profile, active_period):
    """
    Calculate main card display data using server time.
    Returns status, label, value, subtitle, and button text.
    """

    today = now().date()
    late_days = profile.get_late_period_days()

    # Period is currently active
    if active_period:
        start_str = active_period.start_date.strftime('%b %d')
        end_str = active_period.end_date.strftime('%b %d, %Y')

        return {
            'card_status': 'period_active',
            'card_label': 'Current Period',
            'card_value': 'In Progress',
            'card_subtitle': f"{start_str} - {end_str}",
            'card_button_text': 'End Period',
        }

    # Period is late
    if late_days and late_days > 0:
        day_word = 'Day' if late_days == 1 else 'Days'
        subtitle = 'Please start your period when it arrives'

        if profile.next_period_start_date:
            expected = profile.next_period_start_date.strftime('%b %d, %Y')
            subtitle = f"Expected: {expected}"

        return {
            'card_status': 'period_late',
            'card_label': 'Period Late',
            'card_value': f"{late_days} {day_word}",
            'card_subtitle': subtitle,
            'card_button_text': 'Start Period',
        }

    # In fertile window
    if profile.is_fertile_today:
        fertile_start = profile.fertile_window_start
        fertile_end = profile.fertile_window_end

        if fertile_start and fertile_end:
            start_str = fertile_start.strftime('%b %d')
            end_str = fertile_end.strftime('%b %d, %Y')

            days_left = (fertile_end - today).days
            if days_left >= 0:
                return {
                    'card_status': 'fertile_window',
                    'card_label': 'Fertile Window Ends',
                    'card_value': (
                        f"{days_left} {'Day' if days_left == 1 else 'Days'}"
                        if days_left > 0 else 'Today'),
                    'card_subtitle': f"{start_str} - {end_str}",
                    'card_button_text': 'View History',
                }

    # Determine next event
    next_event_days = None
    next_event_type = None
    next_event_date = None

    # Check ovulation
    if profile.ovulation_date and profile.ovulation_date >= today:
        days_to_ovulation = (profile.ovulation_date - today).days
        if days_to_ovulation >= 0:
            next_event_days = days_to_ovulation
            next_event_type = 'Ovulation'
            next_event_date = profile.ovulation_date

    # Check next period
    if profile.next_period_start_date and profile.next_period_start_date >= today:
        days_to_period = (profile.next_period_start_date - today).days
        if days_to_period >= 0:
            if next_event_days is None or days_to_period < next_event_days:
                next_event_days = days_to_period
                next_event_type = 'Next Period'
                next_event_date = profile.next_period_start_date

    # Format next event
    if next_event_days is not None and next_event_type and next_event_date:
        if next_event_days == 0:
            value = 'Today'
        elif next_event_days == 1:
            value = '1 Day Left'
        else:
            value = f"{next_event_days} Days Left"

        expected = next_event_date.strftime('%b %d, %Y')

        return {
            'card_status': 'upcoming_ovulation' if next_event_type == 'Ovulation' else 'upcoming_period',
            'card_label': next_event_type,
            'card_value': value,
            'card_subtitle': f"Expected: {expected}",
            'card_button_text': 'Start Period',
        }

    # No data available
    return {
        'card_status': 'no_data',
        'card_label': 'Next Event',
        'card_value': 'Not Available',
        'card_subtitle': 'Start tracking your periods',
        'card_button_text': 'Start Period',
    }


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


def get_current_period_status(profile):
    """
    Get the current period status for a customer
    """

    active_period = Period.get_active_period(profile.customer)

    # Calculate main card display data
    card_data = calculate_main_card_display(profile, active_period)

    return {
        'active_period': active_period,
        'is_fertile': profile.is_fertile_today,
        'pregnancy_chance': profile.pregnancy_chance_today,
        'next_period_date': profile.next_period_start_date,
        'ovulation_date': profile.ovulation_date,
        'fertile_window_start': profile.fertile_window_start,
        'fertile_window_end': profile.fertile_window_end,
        'avg_cycle_length': profile.avg_cycle_length,
        'avg_period_length': profile.avg_period_length,
        'late_period_days': profile.get_late_period_days(),
        **card_data,  # Add card display data
    }
