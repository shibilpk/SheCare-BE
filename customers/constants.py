from django.db import models


class WeightUnisChoices(models.TextChoices):
    KG = "kg", "KG"
    LB = "lb", "LB"


class LanguageChoices(models.TextChoices):
    ENGLISH = "en", "English"
    MALAYALAM = "ml", "Malayalam"
    HINDI = "hi", "Hindi"
    TAMIL = "ta", "Tamil"
    KANNADA = "kn", "Kannada"
    TELUGU = "te", "Telugu"


class TimezoneChoices(models.TextChoices):
    ASIA_KOLKATA = "Asia/Kolkata", "India (IST)"
    ASIA_DUBAI = "Asia/Dubai", "UAE (GST)"
    ASIA_SINGAPORE = "Asia/Singapore", "Singapore (SGT)"
    ASIA_TOKYO = "Asia/Tokyo", "Japan (JST)"
    ASIA_HONG_KONG = "Asia/Hong_Kong", "Hong Kong (HKT)"
    EUROPE_LONDON = "Europe/London", "UK (GMT/BST)"
    EUROPE_PARIS = "Europe/Paris", "Central Europe (CET)"
    AMERICA_NEW_YORK = "America/New_York", "US Eastern (EST/EDT)"
    AMERICA_LOS_ANGELES = "America/Los_Angeles", "US Pacific (PST/PDT)"
    AMERICA_CHICAGO = "America/Chicago", "US Central (CST/CDT)"
    AUSTRALIA_SYDNEY = "Australia/Sydney", "Australia (AEDT)"


class ReminderTypeChoices(models.TextChoices):
    PERIOD = "period", "Period Reminder"
    OVULATION = "ovulation", "Ovulation Day"
    FERTILITY = "fertility", "Fertility Window"
    MEDICINE = "medicine", "Take Medicine"
    APPOINTMENT = "appointment", "Doctor Appointment"
    WATER = "water", "Drink Water"


# Default reminder choices that all users get
DEFAULT_REMINDER_CHOICES = [
    {
        "reminder_type": ReminderTypeChoices.PERIOD,
        "title": "Period Reminder",
        "icon": "calendar-1",
        "color": "#F44336",
        "enabled": True,
        "days_advance": 0,
        "time": "09:00 AM",
    },
    {
        "reminder_type": ReminderTypeChoices.OVULATION,
        "title": "Ovulation Day",
        "icon": "heart",
        "color": "#FF9800",
        "enabled": True,
        "days_advance": 1,
        "time": "08:00 AM",
    },
    {
        "reminder_type": ReminderTypeChoices.FERTILITY,
        "title": "Fertility Window",
        "icon": "star",
        "color": "#4CAF50",
        "enabled": True,
        "days_advance": 0,
        "time": "07:00 AM",
    },
    {
        "reminder_type": ReminderTypeChoices.MEDICINE,
        "title": "Take Medicine",
        "icon": "pharmacy",
        "color": "#2196F3",
        "enabled": False,
        "days_advance": 0,
        "time": "08:00 PM",
    },
    {
        "reminder_type": ReminderTypeChoices.APPOINTMENT,
        "title": "Doctor Appointment",
        "icon": "stethoscope",
        "color": "#9C27B0",
        "enabled": False,
        "days_advance": 1,
        "time": "08:00 PM",
    },
    {
        "reminder_type": ReminderTypeChoices.WATER,
        "title": "Drink Water",
        "icon": "glass",
        "color": "#00BCD4",
        "enabled": True,
        "days_advance": 0,
        "time": "10:00 AM",
    },
]


# Helper to get reminder details by reminder_type
def get_reminder_details(reminder_type):
    """Get title, icon, and color for a reminder type"""
    reminder_map = {
        choice["reminder_type"]: choice for choice in DEFAULT_REMINDER_CHOICES
    }
    return reminder_map.get(reminder_type, {
        "title": "Unknown",
        "icon": "bell",
        "color": "#666",
    })

