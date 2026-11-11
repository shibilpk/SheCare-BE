from django.utils.timezone import now

from django.db import models
from bisect import bisect_right
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

    # Reference to last recorded period
    last_period = models.ForeignKey(
        "Period",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profile_reference"
    )

    # Cycle regularity tracking (calculated automatically)
    cycle_regularity = models.CharField(
        max_length=20,
        choices=[
            ('regular', 'Regular'),
            ('irregular', 'Irregular'),
            ('unknown', 'Unknown')
        ],
        default='unknown'
    )
    cycle_variance = models.FloatField(
        null=True,
        blank=True,
        help_text="Standard deviation of cycle lengths"
    )

    def __str__(self):
        return f"{self.customer} Period Profile"

    @property
    def follicular_phase_length(self):
        return self.avg_cycle_length - self.luteal_phase_length

    def get_cycle_regularity(self):
        """Calculate if cycles are regular based on last 6 cycles"""
        from django.db.models import StdDev

        recent_periods = Period.objects.filter(
            customer=self.customer,
            cycle_length__isnull=False
        ).order_by('-start_date')[:6]

        if recent_periods.count() < 3:
            return 'unknown', None

        variance = recent_periods.aggregate(
            stddev=StdDev('cycle_length')
        )['stddev']

        if variance is None:
            return 'unknown', None

        # Regular if standard deviation is less than 3 days
        regularity = 'regular' if variance < 3 else 'irregular'
        return regularity, round(variance, 2)

    @property
    def next_period_start_date(self):
        """Predict next period start date based on last period and cycle length"""
        if not self.last_period:
            return None
        return self.last_period.start_date.date() + timedelta(days=self.avg_cycle_length)

    @property
    def next_period_end_date(self):
        """Predict next period end date"""
        if not self.next_period_start_date:
            return None
        return self.next_period_start_date + timedelta(days=self.avg_period_length - 1)

    @property
    def ovulation_date(self):
        """Predict ovulation date (typically luteal_phase_length days before next period)"""
        if not self.next_period_start_date:
            return None
        return self.next_period_start_date - timedelta(days=self.luteal_phase_length)

    def get_late_period_days(self):
        """Return number of days period is late, or None/0 if not late"""
        if not self.next_period_start_date:
            return None
        days = (now().date() - self.next_period_start_date).days
        # Only return positive values (period is late)
        return days if days > 0 else None

    @property
    def current_cycle_day(self):
        """Return current day of the cycle (1-based)"""
        if not self.last_period:
            return None
        days_since_start = (now().date() - self.last_period.start_date.date()).days
        return days_since_start + 1

    @property
    def days_until_next_period(self):
        """Return days until next predicted period"""
        if not self.next_period_start_date:
            return None
        days = (self.next_period_start_date - now().date()).days
        return days if days > 0 else 0

    @property
    def current_phase(self):
        """
        Return current cycle phase: 'menstrual', 'follicular', 'ovulation', 'luteal'
        """
        if not self.last_period or not self.ovulation_date:
            return None

        today = now().date()
        last_period_end = self.last_period.end_date.date()

        # Menstrual phase: during period
        if self.last_period.start_date.date() <= today <= last_period_end:
            return 'menstrual'

        # Ovulation phase: day of ovulation ± 1 day
        ovulation_start = self.ovulation_date - timedelta(days=1)
        ovulation_end = self.ovulation_date + timedelta(days=1)
        if ovulation_start <= today <= ovulation_end:
            return 'ovulation'

        # Luteal phase: after ovulation until next period
        if self.ovulation_date < today < self.next_period_start_date:
            return 'luteal'

        # Follicular phase: after period ends until ovulation
        if last_period_end < today < self.ovulation_date:
            return 'follicular'

        # If past next predicted period, still in luteal (cycle may be longer)
        if today >= self.next_period_start_date:
            return 'luteal'

        return None

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

    def _cycle_anchor_for(self, target_date):
        """
        Start date of the latest recorded period on or before target_date
        (including an ongoing one), falling back to the profile's last period.
        """
        period = Period.objects.filter(
            customer=self.customer,
            start_date__date__lte=target_date,
        ).order_by('-start_date').first() or self.last_period
        return period.start_date.date() if period else None

    def get_ovulation_date_near(self, target_date):
        """
        Predicted ovulation date of the cycle closest to target_date.
        Cycles are projected forwards/backwards from the last recorded period,
        so this works for past and future dates. None without a last period.
        """
        anchor = self._cycle_anchor_for(target_date)
        if not anchor:
            return None
        return self._ovulation_from_anchor(anchor, target_date)

    def _ovulation_from_anchor(self, anchor, target_date):
        """Ovulation date closest to target_date, projecting cycles from anchor."""
        cycle_length = self.avg_cycle_length
        cycle_index = (target_date - anchor).days // cycle_length
        offset = cycle_length - self.luteal_phase_length
        candidates = [
            anchor + timedelta(days=(cycle_index + k) * cycle_length + offset)
            for k in (-1, 0, 1)
        ]
        return min(candidates, key=lambda d: abs((d - target_date).days))

    def get_cycle_markers(self, start_date, end_date, today=None):
        """
        Calendar markers for every day in [start_date, end_date]:
        recorded periods, predicted (future) periods, ovulation and fertile days.
        Returns {'period': [...], 'future_period': [...], 'ovulation': [...],
        'fertile': [...]} with date objects.
        """
        today = today or timezone.now().date()
        periods = list(
            Period.objects.filter(customer=self.customer)
            .order_by('start_date').values_list('start_date', 'end_date'))
        starts = [start.date() for start, _ in periods]
        period_days = {
            start.date() + timedelta(days=i)
            for start, end in periods
            for i in range((end.date() - start.date()).days + 1)
        }
        fallback = self.last_period.start_date.date() if self.last_period else None

        markers = {
            'period': [], 'future_period': [], 'ovulation': [], 'fertile': []}
        for offset in range((end_date - start_date).days + 1):
            day = start_date + timedelta(days=offset)
            if day in period_days:
                markers['period'].append(day)
                continue
            index = bisect_right(starts, day)
            anchor = starts[index - 1] if index else fallback
            if anchor is None:
                continue
            ovulation = self._ovulation_from_anchor(anchor, day)
            if day == ovulation:
                markers['ovulation'].append(day)
            elif ovulation - timedelta(days=5) <= day <= ovulation + timedelta(days=1):
                markers['fertile'].append(day)
            cycle_day = (day - anchor).days % self.avg_cycle_length
            if day > today and cycle_day < self.avg_period_length:
                markers['future_period'].append(day)
        return markers

    @staticmethod
    def _chance(level, percentage, ovulation_date, target_date):
        days_to_ovulation = (ovulation_date - target_date).days
        return {
            'level': level,
            'percentage': percentage,
            'is_ovulation_day': days_to_ovulation == 0,
            'is_fertile_window': -1 <= days_to_ovulation <= 5,
            'ovulation_date': ovulation_date.isoformat(),
        }

    def get_pregnancy_chance_with_percentage(self, date=None):
        """
        Calculate pregnancy chance with percentage for any date (default today)
        Returns: dict with 'level' ('high', 'medium', 'low') and 'percentage' (0-100)
        """
        today = date or timezone.now().date()
        ovulation_date = self.get_ovulation_date_near(today)
        if not ovulation_date:
            return {
                'level': 'low', 'percentage': 5,
                'is_ovulation_day': False, 'is_fertile_window': False,
                'ovulation_date': None,
            }

        fertile_window_start = ovulation_date - timedelta(days=5)
        fertile_window_end = ovulation_date + timedelta(days=1)

        # High chance: Peak fertility (2 days before to 1 day after ovulation)
        peak_start = ovulation_date - timedelta(days=2)
        peak_end = ovulation_date + timedelta(days=1)
        if peak_start <= today <= peak_end:
            # Calculate percentage based on proximity to ovulation
            days_to_ovulation = abs((ovulation_date - today).days)
            if days_to_ovulation == 0:
                percentage = 90  # Ovulation day
            elif days_to_ovulation == 1:
                percentage = 85  # 1 day before/after ovulation
            else:
                percentage = 75  # 2 days before ovulation
            return self._chance(
                'high', percentage, ovulation_date, today)

        # Medium chance: Early fertile window (3-5 days before ovulation)
        if fertile_window_start <= today <= fertile_window_end:
            days_to_ovulation = (ovulation_date - today).days
            if days_to_ovulation >= 3:
                percentage = 50  # 3-5 days before ovulation
            else:
                percentage = 60  # 2 days before ovulation
            return self._chance(
                'medium', percentage, ovulation_date, today)

        # Medium chance: 1-2 days outside fertile window
        medium_window_start = fertile_window_start - timedelta(days=2)
        medium_window_end = fertile_window_end + timedelta(days=2)
        if medium_window_start <= today <= medium_window_end:
            return self._chance('medium', 30, ovulation_date, today)

        # Low chance: During period or well outside fertile window
        return self._chance('low', 5, ovulation_date, today)


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

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return "{}".format(
            self.customer.user.get_full_name(),
        )

    def get_previous_period(self):
        """Get the period that occurred before this one"""
        return Period.objects.filter(
            customer=self.customer,
            start_date__lt=self.start_date
        ).order_by('-start_date').first()

    def save(self, *args, **kwargs):
        # Calculate period length
        if self.start_date and self.end_date:
            self.period_length = (
                self.end_date.date() - self.start_date.date()
            ).days + 1

        # Calculate cycle length from previous period
        if not self.cycle_length:  # Only calculate if not manually set
            previous_period = self.get_previous_period()
            if previous_period:
                self.cycle_length = (
                    self.start_date.date() -
                    previous_period.start_date.date()
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

    @classmethod
    def get_last_period(cls, customer):
        """Get the most recent period for a customer"""
        return cls.objects.filter(customer=customer).order_by('-start_date').first()
