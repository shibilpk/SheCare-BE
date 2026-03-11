from django.db import models

from core.models import BaseModel
from general.constants import LanguageChoice, OSType, StaticContentType
from django_editorjs import EditorJsField


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


class DailyTip(BaseModel):
    date = models.DateField(unique=True)
    short_description = models.TextField(blank=True)
    long_description = models.TextField(blank=True)
    language = models.CharField(
        max_length=10, choices=LanguageChoice.choices,
        default=LanguageChoice.ENGLISH
    )

    def __str__(self):
        return str(self.date)


class BlogPost(BaseModel):
    title = models.CharField(max_length=255)
    short_description = models.TextField(blank=True, null=True)
    content = EditorJsField(
        editorjs_config={
            "tools": {
                "Link": {
                    "config": {
                        "endpoint":
                            '/linkfetching/'
                    }
                },
                "Image": {
                    "config": {
                        "endpoints": {
                            "byFile": '/uploadi/',
                            "byUrl": '/uploadi/'
                        },

                    }
                },
                "Attaches": {
                    "config": {
                        "endpoint": '/uploadf/'
                    }
                }
            }
        }
    )

    author = models.CharField(max_length=255)
    published_date = models.DateField()

    def __str__(self):
        return self.title


# to Save Help and support, Privacy policy and Terms and conditions content in DB
class StaticContent(BaseModel):
    content_type = models.CharField(
        max_length=50, unique=True,
        choices=StaticContentType.choices
    )
    content = EditorJsField()

    def __str__(self):
        return self.content_type


class ContactUs(BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Contact Us"
        verbose_name_plural = "Contact Us Submissions"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Feedback(BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    rating = models.PositiveIntegerField(
        help_text="Rating from 1 to 5"
    )
    feedback_type = models.CharField(
        max_length=50,
        choices=[
            ('bug', 'Bug Report'),
            ('feature', 'Feature Request'),
            ('improvement', 'Improvement'),
            ('general', 'General Feedback'),
        ],
        default='general'
    )
    message = models.TextField()
    is_reviewed = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback Submissions"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.feedback_type} ({self.rating}⭐)"
