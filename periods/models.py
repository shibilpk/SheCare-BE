from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


from core.models import BaseModel


class PeriodProfile(models.Model):
    customer = models.OneToOneField(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="period_profile"
    )

    # User preference
    use_average_cycle = models.BooleanField(default=False)

    # Cycle data (may be user-set or averaged)
    avg_cycle_length = models.PositiveIntegerField(default=28)
    avg_period_length = models.PositiveIntegerField(default=5)
    luteal_phase_length = models.PositiveIntegerField(
        default=14, validators=[MinValueValidator(12), MaxValueValidator(16)]
    )

    # Last known data
    last_period_end_date = models.DateField(null=True, blank=True)
    next_period_start_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer} Period Profile"

    @property
    def follicular_phase_length(self):
        return self.avg_cycle_length - self.luteal_phase_length

    @property
    def ovulation_date(self):
        if not self.next_period_start_date:
            return None
        return (
            self.next_period_start_date -
            timedelta(days=self.luteal_phase_length)
        )

    @property
    def fertile_window_start(self):
        if not self.ovulation_date:
            return None
        return self.ovulation_date - timedelta(days=5)

    @property
    def fertile_window_end(self):
        if not self.ovulation_date:
            return None
        return self.ovulation_date + timedelta(days=1)

    @property
    def is_fertile_today(self):
        today = timezone.now().date()
        return (
            self.fertile_window_start <= today <= self.fertile_window_end
        )


class Period(BaseModel):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    period_length = models.PositiveIntegerField(null=True, blank=True)
    cycle_length = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    previous_period = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return "{}".format(
            self.customer.user.get_full_name(),
        )

    def save(self, *args, **kwargs):
        # Calculate period length
        if self.start_date and self.end_date:
            self.period_length = (
                self.end_date.date() - self.start_date.date()
            ).days + 1

        # Calculate cycle length if there's a previous period
        if self.previous_period:
            self.cycle_length = (
                self.start_date.date() -
                self.previous_period.start_date.date()
            ).days

        # Deactivate other active periods for the same customer
        if self.is_active:
            Period.objects.filter(
                customer=self.customer,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)

        super().save(*args, **kwargs)

    @classmethod
    def get_active_period(cls, customer):
        return cls.objects.filter(
            customer=customer,
            is_active=True
        ).first()
