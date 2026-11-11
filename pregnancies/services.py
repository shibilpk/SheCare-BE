"""
Pregnancy dashboard calculations.

Everything here is derived from data the customer already logs elsewhere
(weight entries, hydration, sleep, exercise, nutrition, daily check-ins) plus a
static week-by-week baby development table.
"""
from datetime import date, timedelta

from django.db.models import Sum

from activities.constants import SYMPTOMS
from activities.models import (
    ExerciseLog, HydrationLog, NutritionGoal, NutritionLog, SleepLog)
from customers.models import DailyEntry, WeightEntry
from pregnancies.models import Appointment

PREGNANCY_DAYS = 280
TOTAL_WEEKS = 40
EXERCISE_WEEKLY_GOAL_MIN = 150
SLEEP_GOAL_HOURS = 8.0

# week: (size comparison, length cm, weight g, development note)
# Approximate averages commonly used in pregnancy-tracking literature.
BABY_DEVELOPMENT = {
    4: ('poppy seed', 0.1, 0, 'The embryo is implanting in the uterus'),
    5: ('sesame seed', 0.2, 0, 'The heart and neural tube are forming'),
    6: ('lentil', 0.6, 0, 'A tiny heartbeat can often be detected'),
    7: ('blueberry', 1.3, 1, 'Arm and leg buds are growing'),
    8: ('raspberry', 1.6, 1, 'Fingers and toes are starting to form'),
    9: ('cherry', 2.3, 2, 'All essential organs have begun to form'),
    10: ('strawberry', 3.1, 4, 'Vital organs are starting to function'),
    11: ('fig', 4.1, 7, 'Baby is moving, though you cannot feel it yet'),
    12: ('lime', 5.4, 14, 'Reflexes are developing; fingers can curl'),
    13: ('lemon', 7.4, 23, 'Vocal cords are forming'),
    14: ('peach', 8.7, 43, 'Baby can make facial expressions'),
    15: ('apple', 10.1, 70, 'Bones are getting harder'),
    16: ('avocado', 11.6, 100, 'Eyes can sense light'),
    17: ('pear', 13.0, 140, 'Fat stores are starting to develop'),
    18: ('bell pepper', 14.2, 190, 'Ears are in position; baby may hear sounds'),
    19: ('mango', 15.3, 240, 'A protective coating (vernix) forms on the skin'),
    20: ('banana', 25.6, 300, 'Halfway there! You may feel kicks'),
    21: ('carrot', 26.7, 360, 'Baby is swallowing amniotic fluid'),
    22: ('papaya', 27.8, 430, 'Senses of touch and taste are developing'),
    23: ('grapefruit', 28.9, 501, 'Baby can hear your voice'),
    24: ('cantaloupe', 30.0, 600, 'Lungs are developing'),
    25: ('cauliflower', 34.6, 660, 'Baby responds to familiar voices'),
    26: ('lettuce', 35.6, 760, 'Eyes begin to open'),
    27: ('cabbage', 36.6, 875, 'Brain activity is increasing rapidly'),
    28: ('eggplant', 37.6, 1005, 'Baby can blink and may dream'),
    29: ('butternut squash', 38.6, 1153, 'Muscles and lungs keep maturing'),
    30: ('cucumber', 39.9, 1319, 'Baby is gaining weight quickly'),
    31: ('coconut', 41.1, 1502, 'All five senses are working'),
    32: ('squash', 42.4, 1702, 'Baby is practising breathing'),
    33: ('pineapple', 43.7, 1918, 'Bones are hardening, except the skull'),
    34: ('melon', 45.0, 2146, 'The central nervous system is maturing'),
    35: ('honeydew', 46.2, 2383, 'Most growth now is weight gain'),
    36: ('romaine lettuce', 47.4, 2622, 'Baby may settle head-down'),
    37: ('swiss chard', 48.6, 2859, 'Baby is considered early term'),
    38: ('leek', 49.8, 3083, 'Organs are ready for life outside'),
    39: ('watermelon', 50.7, 3288, 'Baby is full term'),
    40: ('pumpkin', 51.2, 3462, 'Your due date is here!'),
}

SYMPTOM_NAMES = {item['id']: item['name'] for item in SYMPTOMS}


def pregnancy_start(pregnancy):
    return pregnancy.due_date - timedelta(days=PREGNANCY_DAYS)


def week_for(pregnancy, on_date):
    return max(0, (on_date - pregnancy_start(pregnancy)).days // 7)


def trimester_for(week):
    if week < 14:
        return 1
    if week < 28:
        return 2
    return 3


def baby_for_week(week):
    clamped = max(4, min(week, TOTAL_WEEKS))
    size, length_cm, weight_g, note = BABY_DEVELOPMENT[clamped]
    return {
        'week': clamped,
        'size_comparison': size,
        'length_cm': length_cm,
        'weight_g': weight_g,
        'development': note,
    }


def _weight_kg(entry):
    value = float(entry.weight)
    return round(value * 0.453592 if entry.unit == 'lb' else value, 1)


def recommended_gain(bmi):
    """IOM gestational weight gain guidance by pre-pregnancy BMI."""
    if bmi is None:
        return '11.5-16 kg'
    if bmi < 18.5:
        return '12.5-18 kg'
    if bmi < 25:
        return '11.5-16 kg'
    if bmi < 30:
        return '7-11.5 kg'
    return '5-9 kg'


def maternal_weight(customer, pregnancy):
    start = pregnancy_start(pregnancy)
    entries = list(WeightEntry.objects.filter(
        customer=customer, is_deleted=False
    ).order_by('entry_date', 'time_stamp'))
    if not entries:
        return {
            'pre_pregnancy_weight_kg': None,
            'current_weight_kg': None,
            'weight_gain_kg': None,
            'recommended_gain': recommended_gain(None),
        }, []

    before = [e for e in entries if e.entry_date <= start]
    baseline = before[-1] if before else entries[0]
    current = entries[-1]
    pre_kg = _weight_kg(baseline)
    current_kg = _weight_kg(current)

    bmi = None
    if customer.height:
        height_m = float(customer.height) / 100
        if height_m > 0:
            bmi = pre_kg / (height_m * height_m)

    # Latest weight per pregnancy week, for the progression chart
    by_week = {}
    for e in entries:
        if e.entry_date >= start:
            by_week[week_for(pregnancy, e.entry_date)] = _weight_kg(e)
    series = [{'week': w, 'weight_kg': kg} for w, kg in sorted(by_week.items())]

    return {
        'pre_pregnancy_weight_kg': pre_kg,
        'current_weight_kg': current_kg,
        'weight_gain_kg': round(current_kg - pre_kg, 1),
        'recommended_gain': recommended_gain(bmi),
    }, series


def last_7_days(today):
    return [today - timedelta(days=i) for i in range(6, -1, -1)]


def health_metrics(customer, today):
    """Each metric is the share (0-1) of its goal reached over the last 7 days.
    Days with nothing logged count as 0."""
    days = last_7_days(today)
    start = days[0]

    hydration = {
        h.date: min(1.0, h.amount_ml / h.daily_goal_ml) if h.daily_goal_ml else 0
        for h in HydrationLog.objects.filter(
            customer=customer, date__range=(start, today))
    }
    sleep = {
        s.date: min(1.0, float(s.duration_hours) / SLEEP_GOAL_HOURS)
        for s in SleepLog.objects.filter(
            customer=customer, date__range=(start, today))
    }
    goal = NutritionGoal.objects.filter(customer=customer).first()
    calorie_goal = goal.calories if goal and goal.calories else 2000
    nutrition = {
        row['date']: min(1.0, (row['total'] or 0) / calorie_goal)
        for row in NutritionLog.objects.filter(
            customer=customer, date__range=(start, today)
        ).values('date').annotate(total=Sum('calories'))
    }
    exercise_minutes = ExerciseLog.objects.filter(
        customer=customer, date__range=(start, today)
    ).aggregate(total=Sum('minutes'))['total'] or 0
    checkin_days = DailyEntry.objects.filter(
        customer=customer, date__range=(start, today)).count()

    def avg(values):
        return round(sum(values.get(d, 0) for d in days) / 7, 2)

    return {
        'nutrition': avg(nutrition),
        'hydration': avg(hydration),
        'sleep': avg(sleep),
        'exercise': round(min(1.0, exercise_minutes / EXERCISE_WEEKLY_GOAL_MIN), 2),
        'wellness': round(min(1.0, checkin_days / 7), 2),
    }


def activity_last_7_days(customer, today):
    days = last_7_days(today)
    totals = {
        row['date']: row['total'] or 0
        for row in ExerciseLog.objects.filter(
            customer=customer, date__range=(days[0], today)
        ).values('date').annotate(total=Sum('minutes'))
    }
    return [
        {'date': d, 'label': d.strftime('%a'), 'minutes': totals.get(d, 0)}
        for d in days
    ]


def symptom_trends(customer, pregnancy, today, weeks=6):
    current_week = week_for(pregnancy, today)
    first_week = max(0, current_week - weeks + 1)
    since = pregnancy_start(pregnancy) + timedelta(weeks=first_week)
    entries = DailyEntry.objects.filter(
        customer=customer, date__range=(since, today))

    per_week = dict.fromkeys(range(first_week, current_week + 1), 0)
    recent_counts = {}
    recent_since = today - timedelta(days=6)
    for entry in entries:
        symptoms = entry.symptoms or []
        w = week_for(pregnancy, entry.date)
        if w in per_week:
            per_week[w] += len(symptoms)
        if entry.date >= recent_since:
            for sid in symptoms:
                recent_counts[sid] = recent_counts.get(sid, 0) + 1

    recent = sorted(recent_counts.items(), key=lambda kv: -kv[1])[:3]
    return (
        [{'week': w, 'count': c} for w, c in sorted(per_week.items())],
        [
            {'id': sid, 'name': SYMPTOM_NAMES.get(sid, 'Symptom'), 'days': c}
            for sid, c in recent
        ],
    )


def today_snapshot(customer, today):
    hydration = HydrationLog.objects.filter(
        customer=customer, date=today).first()
    sleep = SleepLog.objects.filter(customer=customer, date=today).first()
    entry = DailyEntry.objects.filter(customer=customer, date=today).first()
    week_start = today - timedelta(days=today.weekday())
    exercise_week = ExerciseLog.objects.filter(
        customer=customer, date__range=(week_start, today)
    ).aggregate(total=Sum('minutes'))['total'] or 0
    return {
        'water_glasses': hydration.glasses_count if hydration else 0,
        'water_goal_glasses': (
            round(hydration.daily_goal_ml / hydration.glass_size_ml)
            if hydration and hydration.glass_size_ml else 8),
        'sleep_hours': float(sleep.duration_hours) if sleep else None,
        'exercise_minutes_week': exercise_week,
        'mood_ids': entry.moods if entry else [],
    }


def build_dashboard(customer, pregnancy, today=None):
    today = today or date.today()
    days_in = (today - pregnancy_start(pregnancy)).days
    current_week = max(0, min(days_in // 7, 42))
    maternal, weight_series = maternal_weight(customer, pregnancy)
    symptoms_by_week, recent_symptoms = symptom_trends(
        customer, pregnancy, today)
    upcoming = Appointment.objects.filter(
        customer=customer, date__gte=today, is_completed=False
    ).order_by('date', 'time').first()

    growth_weeks = [w for w in range(12, TOTAL_WEEKS + 1, 4)
                    if w <= max(current_week + 4, 16)]

    return {
        'pregnancy': {
            'id': pregnancy.id,
            'due_date': pregnancy.due_date,
            'start_date': pregnancy_start(pregnancy),
            'baby_name': pregnancy.baby_name,
            'current_week': current_week,
            'current_day': max(0, days_in) % 7,
            'trimester': trimester_for(current_week),
            'days_remaining': max(0, (pregnancy.due_date - today).days),
            'total_weeks': TOTAL_WEEKS,
            'progress_percent': min(100, round(
                max(0, days_in) / PREGNANCY_DAYS * 100)),
        },
        'baby': baby_for_week(current_week),
        'baby_growth': [
            {'week': w, 'weight_g': BABY_DEVELOPMENT[w][2]}
            for w in growth_weeks
        ],
        'maternal': maternal,
        'weight_series': weight_series,
        'today': today_snapshot(customer, today),
        'health_metrics': health_metrics(customer, today),
        'activity_last_7_days': activity_last_7_days(customer, today),
        'symptoms_by_week': symptoms_by_week,
        'recent_symptoms': recent_symptoms,
        'upcoming_appointment': upcoming,
    }
