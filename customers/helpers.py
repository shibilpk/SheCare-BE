import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.helpers import normalize_number


def calculate_age(
    date_of_birth: date | None,
    *,
    timezone: str = "UTC",
    feb_29_policy: str = "feb28",  # "feb28" or "mar1"
) -> int | None:
    """
    Calculate age from date_of_birth.

    - Timezone-aware (uses the given IANA timezone)
    - Handles Feb 29 birthdays
    - Returns None if date_of_birth is None
    """

    if date_of_birth is None:
        return None

    tz = ZoneInfo(timezone)
    today = datetime.now(tz).date()

    # Determine effective birthday for the current year
    if date_of_birth.month == 2 and date_of_birth.day == 29:
        if calendar.isleap(today.year):
            effective_birthday = date(today.year, 2, 29)
        else:
            if feb_29_policy == "mar1":
                effective_birthday = date(today.year, 3, 1)
            else:  # default: feb28
                effective_birthday = date(today.year, 2, 28)
    else:
        effective_birthday = date(
            today.year,
            date_of_birth.month,
            date_of_birth.day,
        )

    age = today.year - date_of_birth.year

    if today < effective_birthday:
        age -= 1

    return age


def bmi_health_summary(weight_kg, height_cm):
    height_m = height_cm / (100.0)

    # Standard BMI
    bmi = weight_kg / (height_m ** 2)

    # Oxford (New) BMI
    oxford_bmi = 1.3 * (weight_kg / (height_m ** 2.5))

    # Healthy BMI limits
    min_bmi = 18.5
    max_bmi = 25

    # Healthy weight range
    min_weight = min_bmi * (height_m ** 2)
    max_weight = max_bmi * (height_m ** 2)

    notes = [
        "Healthy BMI: 18.5–25 kg/m²",
        f"Healthy weight: {min_weight:.1f}–{max_weight:.1f} kg"
    ]

    # Weight change needed
    change_msg = None
    if weight_kg < min_weight:
        change_msg = (
            f'Gain "{min_weight - weight_kg:.1f}" kg to reach a healthy weight.')
    elif weight_kg > max_weight:
        change_msg = (
            f'Lose "{weight_kg - max_weight:.1f}" kg to reach a healthy weight.')
    else:
        change_msg = "You are already within the healthy weight range."

    if change_msg:
        notes.append(change_msg)

    # Oxford BMI status (UNCHANGED logic)
    if oxford_bmi < 16:
        status = "Severe Thinness"
        status_badge_color = "#e74c3c"
    elif 16 <= oxford_bmi < 17:
        status = "Moderate Thinness"
        status_badge_color = "#f1c40f"
    elif 17 <= oxford_bmi < 18.5:
        status = "Mild Thinness"
        status_badge_color = "#f1c40f"
    elif 18.5 <= oxford_bmi < 25:
        status = "Healthy weight"
        status_badge_color = "#2ecc71"
    elif 25 <= oxford_bmi < 30:
        status = "Overweight"
        status_badge_color = "#e67e22"
    elif 30 <= oxford_bmi < 35:
        status = "Obese Class I"
        status_badge_color = "#e67e22"
    elif 35 <= oxford_bmi < 40:
        status = "Obese Class II"
        status_badge_color = "#e74c3c"
    else:
        status = "Morbidly Obese"
        status_badge_color = "#e74c3c"

    return {
        "bmi": normalize_number(round(bmi, 1), fx_place=1),
        "notes": notes,
        "new_bmi": normalize_number(round(oxford_bmi, 1), fx_place=1),
        "status": status,
        "status_badge_color": status_badge_color,
    }
