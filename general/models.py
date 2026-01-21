from django.db import models

from general.constants import OSType


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
