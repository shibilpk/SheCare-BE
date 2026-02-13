from django.db import models

from general.constants import LanguageChoice, OSType


class AppVersion(models.Model):

    version = models.CharField(max_length=20)
    min_version = models.CharField(max_length=20)
    release_date = models.DateField(auto_now_add=True)
    force_update = models.BooleanField(default=False)
    os = models.CharField(max_length=10, unique=True, choices=OSType.choices)
    download_url = models.URLField(max_length=400, blank=True)
    release_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Version {self.version} released on {self.release_date}"


class AppAdminSettings(models.Model):
    no_avg_period_months = models.PositiveIntegerField(
        default=6,
        help_text=("Number of months to consider for average period "
                   "calculations")
    )

    def __str__(self):
        return "App Admin Settings"

    @classmethod
    def get_settings(cls):
        settings = cls.objects.first()
        return settings if settings else cls.objects.create()


class DailyTip(models.Model):
    date = models.DateField(unique=True)
    short_description = models.TextField(blank=True)
    long_description = models.TextField(blank=True)
    language = models.CharField(
        max_length=10, choices=LanguageChoice.choices,
        default=LanguageChoice.ENGLISH
    )

    def __str__(self):
        return str(self.date)
