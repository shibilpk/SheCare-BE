from django.utils.timezone import now

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

    def get_late_period_days(self):
        """Return number of days period is late, or None/0 if not late"""
        if not self.next_period_start_date:
            return None
        days = (now().date() - self.next_period_start_date).days
        # Only return positive values (period is late)
        return days if days > 0 else None

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
        if not self.fertile_window_start or not self.fertile_window_end:
            return False
        today = timezone.now().date()
        return (
            self.fertile_window_start <= today <= self.fertile_window_end
        )

    @property
    def pregnancy_chance_today(self):
        """
        Calculate pregnancy chance for today based on cycle phase.
        Returns: 'high', 'medium', or 'low'
        """
        if not self.ovulation_date or not self.fertile_window_start or not self.fertile_window_end:
            return 'low'

        today = timezone.now().date()

        # High chance: During fertile window (especially 2 days before ovulation to ovulation day)
        if self.fertile_window_start <= today <= self.fertile_window_end:
            # Peak fertility: 2 days before to 1 day after ovulation
            peak_start = self.ovulation_date - timedelta(days=2)
            peak_end = self.ovulation_date + timedelta(days=1)
            if peak_start <= today <= peak_end:
                return 'high'
            else:
                # Early fertile window (3-5 days before ovulation)
                return 'medium'

        # Medium chance: 1-2 days outside fertile window
        medium_window_start = self.fertile_window_start - timedelta(days=2)
        medium_window_end = self.fertile_window_end + timedelta(days=2)
        if medium_window_start <= today <= medium_window_end:
            return 'medium'

        # Low chance: During period or well outside fertile window
        return 'low'


class Period(BaseModel):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    period_length = models.PositiveIntegerField(
        null=True, blank=True)  # Days between start_date and end_date
    # Days between this period's start and previous period's start
    cycle_length = models.PositiveIntegerField(null=True, blank=True)
    previous_period = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="next_periods"
    )

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return "{}".format(
            self.customer.user.get_full_name(),
        )

    def save(self, *args, **kwargs):
        # Set previous period if not already set and this is a new period
        if not self.pk and not self.previous_period:
            last_period = Period.objects.filter(
                customer=self.customer
            ).order_by('-start_date').first()
            if last_period:
                self.previous_period = last_period

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

        super().save(*args, **kwargs)

    @classmethod
    def get_active_period(cls, customer):
        """Get the period that contains today's date"""
        today = now()
        return cls.objects.filter(
            customer=customer,
            start_date__lte=today,
            end_date__gte=today
        ).order_by('-start_date').first()
