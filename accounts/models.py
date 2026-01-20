from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from core.helpers import generate_otp


class CustomUser(AbstractUser):
    phone = PhoneNumberField(max_length=17, blank=True, null=True)
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )

    def clean(self, *args, **kwargs):

        if (
            self.__class__.objects.filter(
                is_active=True, email__iexact=self.email)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(_("A user with this email already exists."))
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email).lower()
        self.username = self.email if not self.username else self.username
        self.full_clean()

        return super().save(*args, **kwargs)

    @property
    def get_display_name(self):
        return self.get_full_name() or self.email

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.get_display_name


User = get_user_model()


class UserOtp(models.Model):
    otp = models.CharField(max_length=6)
    failed_attempts = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=False)
    phone_number = PhoneNumberField(blank=True)
    email = models.EmailField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.phone_number)

    def send_otp_email(self):
        # TODO: Send OTP via email
        pass

    @classmethod
    def create_email_otp(cls, email, length=6):
        otp = generate_otp(length)

        user_otp, created = cls.objects.update_or_create(
            email=email,
            is_active=True,
            defaults={
                "otp": otp,
                "attempts": 1,
            },
        )

        # Existing active OTP
        if not created:
            if user_otp.attempts >= settings.OTP_CONFIG["MAX_OTP_ATTEMPTS"]:
                raise ValidationError(
                    "Maximum OTP attempts exceeded. Please try again later."
                )

            user_otp.attempts += 1
            user_otp.save(update_fields=["attempts"])

        # Deactivate other OTPs
        cls.objects.filter(email=email).exclude(id=user_otp.id).update(
            is_active=False)

        user_otp.send_otp_email()

        if settings.DEBUG:
            print(f"Email OTP for {email}: {otp}")

        return user_otp
