from django.db import models

from versatileimagefield.fields import VersatileImageField
from django.core.validators import MinValueValidator, MaxValueValidator

from accounts.models import User
from core.helpers import calculate_age
from core.models import BaseModel, CrudUrlMixin, RelatedModal
from datetime import date

from customers.constants import WeightUnisChoices
from customers.helpers import bmi_health_summary


def get_upload_path(instance, filename):
    return f"static/{instance._meta.model_name}/{filename}"


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
            'weight': latest.weight, 'unit': latest.unit} if latest else None

    def get_profile_data(self, request):
        return {

            "email": self.user.email,
            "name": self.user.get_full_name(),
            "phone": str(self.user.phone) if self.user.phone else None,
            "photo": (
                request.build_absolute_uri(self.photo.url)
                if self.photo else None),
            "age": self.age,
            "height": self.height,
            "weight": self.weight,
            "date_of_birth": self.date_of_birth,
        }

    @property
    def bmi(self):
        weight = self.weight['weight']
        unit = self.weight['unit']

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
