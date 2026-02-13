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

