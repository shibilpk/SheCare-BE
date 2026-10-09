from datetime import date, timedelta
from django.db import models
from core.models import BaseModel


class Pregnancy(BaseModel):
    """Model to track customer pregnancy"""
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='pregnancies'
    )

    # Pregnancy status
    is_active = models.BooleanField(
        default=True, help_text="Is this pregnancy currently active")

    # Pregnancy dates
    due_date = models.DateField(help_text="Expected due date")
    last_period = models.ForeignKey(
        'periods.Period',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pregnancies',
        help_text="Last menstrual period (LMP) from period tracking"
    )

    # Baby information
    baby_name = models.CharField(max_length=100, blank=True, default='')

    # Medical information
    doctor_name = models.CharField(max_length=100, blank=True, default='')
    hospital_name = models.CharField(max_length=200, blank=True, default='')

    # Pregnancy outcome flags
    baby_born = models.BooleanField(
        default=False, help_text="Baby has been born")
    pregnancy_lost = models.BooleanField(
        default=False, help_text="Pregnancy was lost/miscarriage")
    mistaken_toggle = models.BooleanField(
        default=False,
        help_text="Pregnancy mode was turned on by mistake"
    )

    # Baby details (filled when baby_born is True)
    child_name = models.CharField(max_length=100, blank=True, default='')
    birth_date = models.DateField(null=True, blank=True)
    birth_weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Birth weight in kg"
    )
    birth_length = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Birth length in cm"
    )
    child_gender = models.CharField(
        max_length=10,
        choices=[('boy', 'Boy'), ('girl', 'Girl'), ('', 'Not specified')],
        blank=True,
        default=''
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'is_active']),
        ]

    def __str__(self):
        return f"{self.customer.user.get_full_name()} - Pregnancy (Due: {self.due_date})"

    def save(self, *args, **kwargs):

        # If marking as born, lost, or mistake, deactivate
        if self.baby_born or self.pregnancy_lost or self.mistaken_toggle:
            self.is_active = False

        # Auto-set due_date if not provided and last_period exists
        if not self.due_date and self.last_period:
            lmp_date = (
                self.last_period.start_date.date()
                if hasattr(self.last_period.start_date, 'date')
                else self.last_period.start_date
            )
            self.due_date = lmp_date + timedelta(days=280)
        elif not self.due_date:
            # If no due_date and no last_period, set a default
            self.due_date = date.today() + timedelta(days=280)

        super().save(*args, **kwargs)

    def generate_due_date_from_lmp(self):
        """Calculate due date based on last menstrual period (LMP)"""
        if self.last_period and self.last_period.start_date and not self.due_date:
            lmp_date = (
                self.last_period.start_date.date()
                if hasattr(self.last_period.start_date, 'date')
                else self.last_period.start_date
            )
            self.due_date = lmp_date + timedelta(days=280)
            self.save()

    @property
    def last_period_date(self):
        """Get last period date from the related Period object"""
        if self.last_period:
            return self.last_period.start_date.date()
        return None

    @property
    def weeks_pregnant(self):
        """Calculate current week of pregnancy based on due date"""
        from datetime import date
        today = date.today()
        days_remaining = (self.due_date - today).days
        weeks_remaining = days_remaining // 7
        current_week = 40 - weeks_remaining
        return max(0, min(current_week, 40))

    @classmethod
    def get_active_pregnancy(cls, customer):
        """Get active pregnancy for a customer"""
        return cls.objects.filter(
            customer=customer,
            is_active=True,
            baby_born=False,
            pregnancy_lost=False,
            mistaken_toggle=False
        ).first()


