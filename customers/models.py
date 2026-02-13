from django.db import models

from versatileimagefield.fields import VersatileImageField
from django.core.validators import MinValueValidator, MaxValueValidator

from accounts.models import User
from core.helpers import normalize_number
from customers.helpers import calculate_age
from core.models import BaseModel, CrudUrlMixin, RelatedModal
from datetime import date

from customers.constants import WeightUnisChoices, LanguageChoices, TimezoneChoices
from customers.helpers import bmi_health_summary


def get_upload_path(instance, filename):
    return f"{instance._meta.model_name}/{filename}"


class Customer(BaseModel, CrudUrlMixin):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="customer", null=True
    )
    photo = VersatileImageField(
        "Photo",
        upload_to=get_upload_path,
        blank=True,
        null=True,
    )
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    height = models.DecimalField(
        verbose_name="Height (cm)",
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )
    language = models.CharField(
        max_length=10,
        choices=LanguageChoices.choices,
        default=LanguageChoices.ENGLISH,
        help_text="Preferred language for the app"
    )
    timezone = models.CharField(
        max_length=50,
        choices=TimezoneChoices.choices,
        default=TimezoneChoices.ASIA_KOLKATA,
        help_text="User's timezone"
    )

    class Crud:
        url_base_name = "customer"

    def __str__(self):
        return str(self.user.get_full_name())

    @property
    def age(self):
        return calculate_age(self.date_of_birth)

    @property
    def weight(self):
        latest = (
            WeightEntry.objects.filter(customer=self)
            .order_by("-entry_date", "-time_stamp")
            .first()
        )
        return {
            'weight': normalize_number(
                latest.weight), 'unit': latest.unit} if latest else None

    def get_profile_data(self, request):

        return {

            "email": self.user.email,
            "name": self.user.get_full_name(),
            "phone": str(self.user.phone) if self.user.phone else None,
            "photo": (
                request.build_absolute_uri(self.photo.url)
                if self.photo else None),
            "age": self.age,
            "height": normalize_number(self.height, fx_place=1),
            "weight": self.weight,
            "date_of_birth": self.date_of_birth,
            "language": self.language,
            "timezone": self.timezone,
        }

    def get_bmi_data(self):
        weight_data = self.weight

        # Return None if no weight entry exists
        if not weight_data:
            return None

        weight = weight_data['weight']
        unit = weight_data['unit']

        if unit == WeightUnisChoices.LB:
            weight = float(weight) * 0.453592  # Convert pounds to kg

        height = self.height
        if weight and height:
            return bmi_health_summary(float(weight), float(height))
        return None


class WeightEntry(RelatedModal):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="weight_entries"
    )
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    entry_date = models.DateField()
    time_stamp = models.TimeField(auto_now_add=True)
    unit = models.CharField(
        max_length=100, blank=True, null=True,
        choices=WeightUnisChoices.choices)

    def __str__(self):
        return "{} - {} kg on {}".format(
            self.customer.user.get_full_name(),
            self.weight,
            self.entry_date,
        )

    class Meta:
        ordering = ['-entry_date', '-time_stamp']


class CustomerDiaryEntry(BaseModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="diary_entries"
    )
    entry_date = models.DateField()
    content = models.TextField()

    def __str__(self):
        return "{} - Entry on {}".format(
            self.customer.user.get_full_name(),
            self.entry_date,
        )

    class Meta:
        ordering = ['-entry_date']
