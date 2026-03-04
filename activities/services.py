"""
Service layer for activities app business logic
"""
from typing import List, Dict, Optional, Tuple
from datetime import date
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from activities.models import Medication, MedicationLog


User = get_user_model()


class MedicationService:
    """Service class to handle medication-related business logic"""

    @staticmethod
    def get_medication_by_id(
        medication_id: int, user: 'User'
    ) -> Optional[Medication]:
        """Get a specific medication for a user"""
        try:
            return Medication.objects.get(id=medication_id, user=user)
        except Medication.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_medication(
        user: 'User', medication_data: Dict
    ) -> Medication:
        """Create a new medication"""
        return Medication.objects.create(
            user=user,
            **medication_data
        )

    @staticmethod
    @transaction.atomic
    def update_medication(
        medication: Medication, medication_data: Dict
    ) -> Medication:
        """Update an existing medication"""
        for field, value in medication_data.items():
            setattr(medication, field, value)
        medication.save()
        return medication

    @staticmethod
    @transaction.atomic
    def soft_delete_medication(medication: Medication) -> None:
        """Soft delete a medication by marking it as inactive"""
        medication.is_active = False
        medication.save()

    @staticmethod
    def get_medications_with_doses(
        user: 'User', target_date: date
    ) -> List[Dict]:
        """
        Get all medications with dose status for a specific date

        Returns medications with their doses and completion status
        """
        medications = Medication.objects.filter(user=user, is_active=True)
        result = []

        for med in medications:
            # Get logs for this medication and date
            logs = MedicationLog.objects.filter(
                medication=med,
                date=target_date
            ).order_by('dose_index')

            # Create a dict for quick lookup
            log_dict = {log.dose_index: log for log in logs}

            # Build doses array
            doses = []
            for idx, time_label in enumerate(med.dose_times):
                log = log_dict.get(idx)
                doses.append({
                    'dose_index': idx,
                    'time': time_label,
                    'taken': log.taken if log else False
                })

            result.append({
                'id': med.id,
                'name': med.name,
                'dosage': med.dosage,
                'frequency': med.frequency_text,
                'color': med.color,
                'doses': doses
            })

        return result

    @staticmethod
    @transaction.atomic
    def toggle_medication_dose(
        medication: Medication,
        target_date: date,
        dose_index: int,
        taken: bool
    ) -> Tuple[MedicationLog, bool]:
        """
        Toggle a medication dose as taken/not taken

        Returns:
            Tuple of (MedicationLog instance, error_message or None)
        """
        # Validate dose_index
        max_index = len(medication.dose_times) - 1
        if dose_index >= len(medication.dose_times):
            raise ValueError(
                f"Invalid dose index: {dose_index}. "
                f"Maximum allowed: {max_index}"
            )

        # Get dose time label
        dose_time = medication.dose_times[dose_index]

        # Get or create the log
        log, created = MedicationLog.objects.get_or_create(
            medication=medication,
            date=target_date,
            dose_index=dose_index,
            defaults={
                'dose_time': dose_time,
                'taken': taken,
                'taken_at': timezone.now() if taken else None,
            }
        )

        if not created:
            # Update existing log
            log.taken = taken
            log.taken_at = timezone.now() if taken else None
            log.save()

        return log, created

    @staticmethod
    def get_medication_stats(
        user: 'User', target_date: date
    ) -> Dict:
        """
        Get medication completion statistics for a specific date

        Returns dict with total/taken doses and completion percent
        """
        # Get all active medications
        medications = Medication.objects.filter(user=user, is_active=True)

        # Calculate total expected doses for the day
        total_doses = sum(med.times_per_period for med in medications)

        # Get all logs for this date that are marked as taken
        taken_doses = MedicationLog.objects.filter(
            medication__user=user,
            medication__is_active=True,
            date=target_date,
            taken=True
        ).count()

        # Calculate completion percentage
        completion_percent = (
            (taken_doses / total_doses * 100) if total_doses > 0 else 0
        )

        return {
            'total_doses': total_doses,
            'taken_doses': taken_doses,
            'completion_percent': round(completion_percent, 2)
        }
