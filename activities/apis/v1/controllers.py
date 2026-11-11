from ninja.errors import HttpError
from ninja_extra import (
    api_controller, http_get, http_post, http_put, http_delete
)
from datetime import date as date_type, timedelta
from general.apis.v1.schemas import SuccessSchema
from accounts.apis.v1.permissions import IsCustomer
from typing import List
from uuid import UUID
from django.db.models import Q, Sum

from activities.constants import (
    MOODS, RATING_SECTIONS, SYMPTOMS, ACTIVITIES,
    INTIMACY_OPTIONS, FLOW_OPTIONS)
from activities.apis.v1.schemas import (
    DailyEntryInputSchema, DailyEntryOutputSchema,
    CalendarMarkersOutputSchema,
    HydrationLogInputSchema, HydrationLogOutputSchema,
    HydrationContentOutputSchema,
    MedicationInputSchema, MedicationOutputSchema,
    MedicationWithDosesOutputSchema, MedicationLogInputSchema,
    MedicationLogOutputSchema, MedicationStatsSchema,
    ErrorResponseSchema,
    NutritionLogInputSchema, NutritionLogOutputSchema,
    NutritionGoalInputSchema, NutritionGoalOutputSchema,
    FoodSuggestionOutputSchema, NutritionSummarySchema,
    FoodSearchResultSchema,
    ExerciseTypeOutputSchema, ExerciseLogInputSchema, ExerciseLogOutputSchema,
    ExerciseWeekSummarySchema,
    SleepLogInputSchema, SleepLogOutputSchema, SleepLogListSchema)
from customers.models import DailyEntry, DiaryEntry
from activities.models import (
    HydrationLog, HydrationContent,
    NutritionLog, NutritionGoal, FoodSuggestion,
    ExerciseType, ExerciseLog, SleepLog)
from activities.services import MedicationService, CalendarMarkerService


@api_controller("activities/", tags=["Daily Actions"])
class ActivitiesAPIController:

    _LOOKUPS = {
        'mood': {item['id']: item for item in MOODS},
        'symptom': {item['id']: item for item in SYMPTOMS},
        'activity': {item['id']: item for item in ACTIVITIES},
        'intimacy': {item['id']: item for item in INTIMACY_OPTIONS},
        'flow': {item['id']: item for item in FLOW_OPTIONS},
    }

    _DIARY_CARD = {
        'icon': 'book',
        'title': 'Diary Entry',
        'value': 'Logged',
        'color': '#D1C4E9',
    }

    # ---- Summary card helpers for daily-entries-detailed ----

    @staticmethod
    def _pregnancy_chance(customer, date_str):
        """Pregnancy chance for the given date, or None without a period profile."""
        profile = getattr(customer, 'period_profile', None)
        if profile is None:
            return None
        try:
            target_date = date_type.fromisoformat(date_str)
        except ValueError:
            return None
        return profile.get_pregnancy_chance_with_percentage(target_date)

    @staticmethod
    def _plural(count, singular, plural=None):
        return singular if count == 1 else (plural or f"{singular}s")

    @staticmethod
    def _group_entry(daily_entry):
        """Selected option ids per category for a daily entry (or none)."""
        return {
            'mood': daily_entry.moods if daily_entry else [],
            'symptom': daily_entry.symptoms if daily_entry else [],
            'activity': daily_entry.activities if daily_entry else [],
            'intimacy': daily_entry.intimacy if daily_entry else [],
            'flow': daily_entry.flow if daily_entry else [],
        }

    @classmethod
    def _emoji_value(cls, items, kind):
        """First 5 emojis of the given items, space separated."""
        lookup = cls._LOOKUPS[kind]
        emojis = [
            lookup.get(item_id, {}).get('emoji') for item_id in items]
        return ' '.join([e for e in emojis if e][:5])

    @classmethod
    def _mood_card(cls, grouped):
        items = grouped['mood']
        if not items:
            return None
        return {
            'icon': '😊',
            'title': f"{len(items)} {cls._plural(len(items), 'Mood')} Added",
            'value': cls._emoji_value(items, 'mood'),
            'color': '#FFE0B2',
        }

    @classmethod
    def _symptom_card(cls, grouped):
        items = grouped['symptom']
        if not items:
            return None
        return {
            'icon': 'thermometer',
            'title': (
                f"{len(items)} {cls._plural(len(items), 'Symptom')} Tracked"),
            'value': f"{len(items)} logged",
            'color': '#FFCDD2',
        }

    @classmethod
    def _activity_card(cls, grouped):
        items = grouped['activity']
        if not items:
            return None
        return {
            'icon': '💪',
            'title': (
                f"{len(items)} "
                f"{cls._plural(len(items), 'Activity', 'Activities')}"),
            'value': cls._emoji_value(items, 'activity'),
            'color': '#C8E6C9',
        }

    @classmethod
    def _single_choice_card(
            cls, grouped, kind, title, default_icon, default_color):
        """Card for types where only the first selected option is shown."""
        items = grouped[kind]
        if not items:
            return None
        data = cls._LOOKUPS[kind].get(items[0], {})
        return {
            'icon': data.get('emoji', default_icon),
            'title': title,
            'value': data.get('label', 'Logged'),
            'color': data.get('color', default_color),
        }

    @classmethod
    def _intimacy_card(cls, grouped):
        return cls._single_choice_card(
            grouped, 'intimacy', 'Intimacy', '❤️', '#F8BBD0')

    @classmethod
    def _flow_card(cls, grouped):
        return cls._single_choice_card(
            grouped, 'flow', 'Flow', '💧', '#E1F5FE')

    @classmethod
    def _ratings_card(cls, ratings):
        if not ratings:
            return None
        average = sum(r.get('rating', 0) for r in ratings) / len(ratings)
        return {
            'icon': 'star',
            'title': f"{len(ratings)} {cls._plural(len(ratings), 'Rating')}",
            'rating': round(average, 1),
            'color': '#FFF9C4',
        }

    @http_get('daily-actions/')
    def get_all_daily_actions(self):
        return {
            "moods": MOODS,
            "symptoms": SYMPTOMS,
            "activities": ACTIVITIES,
            "intimacy_options": INTIMACY_OPTIONS,
            "flow_options": FLOW_OPTIONS,
        }

    @http_get('rating-lists/')
    def get_all_rating_data(self):
        return {
            "heading": "Rate your Body & Mind",
            "sub_heading": "How are you feeling today?",
            "sections": RATING_SECTIONS,
        }

    @http_post('daily-entries/', response=DailyEntryOutputSchema)
    def create_or_update_daily_entry(
            self, request, payload: DailyEntryInputSchema):
        """Create or update a daily entry for the authenticated user"""
        customer = request.user.customer

        # Get or create the daily entry for this date
        daily_entry, _ = DailyEntry.objects.update_or_create(
            customer=customer,
            date=payload.date,
            defaults={
                'moods': payload.moods,
                'symptoms': payload.symptoms,
                'activities': payload.activities,
                'intimacy': payload.intimacy,
                'flow': payload.flow,
                'ratings': payload.ratings,
            }
        )

        return daily_entry

    @http_get('daily-entries/{date}/',
              response={200: DailyEntryOutputSchema, 404: dict})
    def get_daily_entry(self, request, date: str):
        """Get daily entry for a specific date"""
        customer = request.user.customer

        try:
            daily_entry = DailyEntry.objects.get(customer=customer, date=date)
            return 200, daily_entry
        except DailyEntry.DoesNotExist:
            return 404, {"detail": "No entry found for this date"}

    MAX_CALENDAR_RANGE_DAYS = 400

    @http_get('calendar-markers/', response={200: CalendarMarkersOutputSchema})
    def get_calendar_markers(
            self, request, start_date: date_type, end_date: date_type):
        """
        Dates to mark on the calendar between start_date and end_date:
        period, future_period, ovulation, fertile, pregnant (due date),
        medication, love (intimacy) and diary.
        """
        if end_date < start_date:
            raise HttpError(400, "end_date must not be before start_date")
        if (end_date - start_date).days > self.MAX_CALENDAR_RANGE_DAYS:
            raise HttpError(
                400,
                f"Range must not exceed {self.MAX_CALENDAR_RANGE_DAYS} days")

        return CalendarMarkerService.get_markers(
            request.user.customer, start_date, end_date)

    @http_get('daily-entries-detailed/{date}/',
              response={200: dict})
    def get_daily_entries_detailed(self, request, date: str):
        """Get daily entry summary for a specific date"""
        customer = request.user.customer

        daily_entry = DailyEntry.objects.filter(
            customer=customer, date=date).first()
        diary_entry_exists = DiaryEntry.objects.filter(
            customer=customer, entry_date=date).exists()

        ratings = daily_entry.ratings if daily_entry else []
        grouped = self._group_entry(daily_entry)

        cards = [
            self._mood_card(grouped),
            self._symptom_card(grouped),
            self._activity_card(grouped),
            self._intimacy_card(grouped),
            self._flow_card(grouped),
            self._ratings_card(ratings),
        ]
        if diary_entry_exists:
            cards.append(self._DIARY_CARD)

        # Drop empty sections and number the remaining cards sequentially
        summary_cards = [
            {'id': card_id, **card}
            for card_id, card in enumerate(filter(None, cards), start=1)
        ]

        return 200, {
            'id': daily_entry.id if daily_entry else None,
            'date': str(daily_entry.date) if daily_entry else date,
            'summary_cards': summary_cards,
            'pregnancy_chance': self._pregnancy_chance(customer, date),
            'created_at': (
                daily_entry.created_at.isoformat() if daily_entry else None),
        }


@api_controller("hydration/", tags=["Hydration"])
class HydrationAPIController:

    # Hydration Endpoints
    @http_get(
        'hydration/{date}/',
        response={200: HydrationLogOutputSchema, 404: dict}
    )
    def get_hydration_log(self, request, date: str):
        """Get hydration log for a specific date"""
        customer = request.user.customer

        try:
            hydration_log = HydrationLog.objects.get(
                customer=customer, date=date
            )
            return 200, hydration_log
        except HydrationLog.DoesNotExist:
            return 404, {"detail": "No hydration log found for this date"}

    @http_post('hydration/', response=HydrationLogOutputSchema)
    def create_or_update_hydration_log(
            self, request, payload: HydrationLogInputSchema):
        """Create or update hydration log for a specific date"""
        customer = request.user.customer

        hydration_log, created = HydrationLog.objects.get_or_create(
            customer=customer,
            date=payload.date,
            defaults={
                'amount_ml': payload.amount_ml,
                'glass_size_ml': payload.glass_size_ml,
                'daily_goal_ml': payload.daily_goal_ml,
            }
        )

        if not created:
            # Update existing log
            if payload.amount_ml is not None:
                hydration_log.amount_ml = payload.amount_ml
            if payload.glass_size_ml is not None:
                hydration_log.glass_size_ml = payload.glass_size_ml
            if payload.daily_goal_ml is not None:
                hydration_log.daily_goal_ml = payload.daily_goal_ml
            hydration_log.save()

        return hydration_log

    @http_get('hydration-content/', response=HydrationContentOutputSchema)
    def get_hydration_content(self, request):
        """Get hydration benefits and tips"""
        benefits = HydrationContent.objects.filter(
            content_type='benefit',
            is_active=True
        ).values('id', 'content_type', 'icon', 'text', 'order')

        tips = HydrationContent.objects.filter(
            content_type='tip',
            is_active=True
        ).values('id', 'content_type', 'icon', 'text', 'order')

        return {
            'benefits': list(benefits),
            'tips': list(tips)
        }


@api_controller("medication/", tags=["Medication"])
class MedicationAPIController:
    """Controller for medication management endpoints"""

    # Error messages
    MEDICATION_NOT_FOUND = "Medication not found"

    def __init__(self):
        self.service = MedicationService()

    @http_get(
        'medications/by-date/{date}/',
        response=List[MedicationWithDosesOutputSchema]
    )
    def get_medications_with_doses(self, request, date: str):
        """Get all medications with their dose status for a specific date"""
        medications_with_doses = self.service.get_medications_with_doses(
            customer=request.user.customer,
            target_date=date
        )
        return medications_with_doses

    @http_post(
        'medications/',
        response={201: MedicationOutputSchema, 400: ErrorResponseSchema}
    )
    def create_medication(self, request, payload: MedicationInputSchema):
        """Create a new medication for the authenticated user"""

        medication_data = payload.dict(exclude_unset=True)
        medication = self.service.create_medication(
            customer=request.user.customer,
            medication_data=medication_data
        )
        return 201, medication

    @http_put(
        'medications/{medication_id}/',
        response={
            200: MedicationOutputSchema,
            404: ErrorResponseSchema,
            400: ErrorResponseSchema
        }
    )
    def update_medication(
        self, request, medication_id: UUID, payload: MedicationInputSchema
    ):
        """Update an existing medication asdasdas asdasds asdasda asdasd asdsadas sadasdas asdsa """
        medication = self.service.get_medication_by_id(
            medication_id, request.user.customer
        )

        if not medication:
            return 404, {
                "error": self.MEDICATION_NOT_FOUND,
                "detail": f"No medication found with ID {medication_id}"
            }

        medication_data = payload.dict(exclude_unset=True)
        updated_medication = self.service.update_medication(
            medication=medication,
            medication_data=medication_data
        )
        return 200, updated_medication

    @http_delete(
        'medications/{medication_id}/',
        response={200: dict, 404: ErrorResponseSchema}
    )
    def delete_medication(self, request, medication_id: UUID):
        """Soft delete a medication by marking it as inactive"""
        medication = self.service.get_medication_by_id(
            medication_id, request.user.customer
        )

        if not medication:
            return 404, {
                "error": self.MEDICATION_NOT_FOUND,
                "detail": f"No medication found with ID {medication_id}"
            }

        self.service.soft_delete_medication(medication)
        return 200, {
            "message": "Medication deleted successfully",
            "medication_id": str(medication_id)
        }

    @http_post(
        'medication-log/',
        response={
            200: MedicationLogOutputSchema,
            404: ErrorResponseSchema,
            400: ErrorResponseSchema
        }
    )
    def toggle_medication_dose(
        self, request, payload: MedicationLogInputSchema
    ):
        """Toggle a medication dose as taken/not taken"""
        medication = self.service.get_medication_by_id(
            payload.medication_id,
            request.user.customer
        )

        if not medication:
            return 404, {
                "error": self.MEDICATION_NOT_FOUND,
                "detail": (
                    f"No medication found with ID "
                    f"{payload.medication_id}"
                )
            }

        try:
            log, _ = self.service.toggle_medication_dose(
                medication=medication,
                target_date=payload.date,
                dose_index=payload.dose_index,
                taken=payload.taken
            )
            return 200, log
        except ValueError as e:
            return 400, {
                "error": "Invalid dose index",
                "detail": str(e)
            }
        except Exception as e:
            return 400, {
                "error": "Failed to log medication dose",
                "detail": str(e)
            }

    @http_get('medication-stats/{date}/', response=MedicationStatsSchema)
    def get_medication_stats(self, request, date: str):
        """Get medication completion statistics for a specific date"""
        stats = self.service.get_medication_stats(
            customer=request.user.customer,
            target_date=date
        )
        return stats


@api_controller("nutrition/", tags=["Nutrition"])
class NutritionAPIController:
    """Controller for nutrition tracking endpoints"""

    @http_get(
        'summary/{date}/',
        response={200: NutritionSummarySchema, 400: ErrorResponseSchema}
    )
    def get_nutrition_summary(self, request, date: str):
        """Get nutrition summary for a specific date"""
        customer = request.user.customer

        # Get or create nutrition goal
        goal, _ = NutritionGoal.objects.get_or_create(customer=customer)

        # Get all logs for the date
        logs = NutritionLog.objects.filter(customer=customer, date=date)

        # Calculate totals
        totals = logs.aggregate(
            calories=Sum('calories'),
            carbs=Sum('carbs'),
            protein=Sum('protein'),
            fat=Sum('fat')
        )

        # Handle None values from empty aggregation
        totals = {
            'calories': totals['calories'] or 0,
            'carbs': totals['carbs'] or 0,
            'protein': totals['protein'] or 0,
            'fat': totals['fat'] or 0,
        }

        # Calculate progress
        progress = {
            'calories': min(100, round((totals['calories'] / goal.calories) * 100, 2)) if goal.calories > 0 and totals['calories'] else 0,
            'carbs': min(100, round((totals['carbs'] / goal.carbs) * 100, 2)) if goal.carbs > 0 and totals['carbs'] else 0,
            'protein': min(100, round((totals['protein'] / goal.protein) * 100, 2)) if goal.protein > 0 and totals['protein'] else 0,
            'fat': min(100, round((totals['fat'] / goal.fat) * 100, 2)) if goal.fat > 0 and totals['fat'] else 0,
        }

        return 200, {
            'date': date,
            'logs': list(logs),
            'goal': goal,
            'totals': totals,
            'progress': progress
        }

    @http_post(
        'logs/',
        response={201: NutritionLogOutputSchema, 400: ErrorResponseSchema}
    )
    def create_nutrition_log(self, request, payload: NutritionLogInputSchema):
        """Create a new nutrition log entry"""
        log = NutritionLog.objects.create(
            customer=request.user.customer,
            **payload.dict()
        )
        return 201, log

    @http_put(
        'logs/{log_id}/',
        response={200: NutritionLogOutputSchema, 404: ErrorResponseSchema}
    )
    def update_nutrition_log(self, request, log_id: int, payload: NutritionLogInputSchema):
        """Update a nutrition log entry"""
        try:
            log = NutritionLog.objects.get(
                id=log_id, customer=request.user.customer)
            for field, value in payload.dict().items():
                setattr(log, field, value)
            log.save()
            return 200, log
        except NutritionLog.DoesNotExist:
            return 404, {
                "error": "Not found",
                "detail": f"No nutrition log found with ID {log_id}"
            }

    @http_delete(
        'logs/{log_id}/',
        response={200: dict, 404: ErrorResponseSchema}
    )
    def delete_nutrition_log(self, request, log_id: int):
        """Delete a nutrition log entry"""
        try:
            log = NutritionLog.objects.get(
                id=log_id, customer=request.user.customer)
            log.delete()
            return 200, {"message": "Nutrition log deleted successfully"}
        except NutritionLog.DoesNotExist:
            return 404, {
                "error": "Not found",
                "detail": f"No nutrition log found with ID {log_id}"
            }

    @http_get('goal/', response=NutritionGoalOutputSchema)
    def get_nutrition_goal(self, request):
        """Get customer's nutrition goal"""
        goal, _ = NutritionGoal.objects.get_or_create(
            customer=request.user.customer)
        return goal

    @http_post('goal/', response=NutritionGoalOutputSchema)
    def update_nutrition_goal(self, request, payload: NutritionGoalInputSchema):
        """Update customer's nutrition goal"""
        goal, _ = NutritionGoal.objects.update_or_create(
            customer=request.user.customer,
            defaults=payload.dict()
        )
        return goal

    @http_get(
        'food-suggestions/',
        response={200: FoodSearchResultSchema, 400: ErrorResponseSchema}
    )
    def search_food_suggestions(
        self, request,
        q: str = '',
        page: int = 1,
        page_size: int = 10
    ):
        """Search food suggestions with pagination"""
        if page < 1:
            return 400, {"error": "Invalid page number", "detail": "Page must be >= 1"}

        if page_size < 1 or page_size > 100:
            return 400, {"error": "Invalid page size", "detail": "Page size must be between 1 and 100"}

        # Build query
        queryset = FoodSuggestion.objects.filter(is_active=True)

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q)
            )

        # Get total count
        total = queryset.count()

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        results = list(queryset[start:end])

        has_next = end < total

        return 200, {
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'has_next': has_next
        }


# Weekly activity target recommended for adults/pregnancy (WHO: 150 min/week)
EXERCISE_WEEKLY_GOAL = {'minutes': 150, 'calories': 500}
SLEEP_GOAL_HOURS = 8.0


def _exercise_log_out(log):
    return {
        'id': log.id,
        'exercise_type_id': log.exercise_type_id,
        'name': log.name,
        'date': log.date,
        'minutes': log.minutes,
        'calories': log.calories,
        'intensity': log.intensity,
    }


@api_controller("exercise/", tags=["Exercise"], permissions=[IsCustomer])
class ExerciseAPIController:
    """Workout logging with a weekly (Mon-Sun) summary."""

    @http_get('types/', response=List[ExerciseTypeOutputSchema])
    def list_exercise_types(self, request, category: str = '', q: str = ''):
        """Exercise catalog, optionally filtered by category / search."""
        qs = ExerciseType.objects.filter(is_active=True)
        if category and category != 'All':
            qs = qs.filter(category=category)
        if q:
            qs = qs.filter(name__icontains=q)
        return list(qs)

    @http_get('summary/{date}/', response=ExerciseWeekSummarySchema)
    def week_summary(self, request, date: date_type):
        """All workouts in the Mon-Sun week containing `date`, with totals."""
        week_start = date - timedelta(days=date.weekday())
        week_end = week_start + timedelta(days=6)
        logs = list(ExerciseLog.objects.filter(
            customer=request.user.customer,
            date__range=(week_start, week_end),
        ))
        totals = {
            'minutes': sum(log.minutes for log in logs),
            'calories': sum(log.calories for log in logs),
        }
        goal = EXERCISE_WEEKLY_GOAL
        return {
            'week_start': week_start,
            'week_end': week_end,
            'logs': [_exercise_log_out(log) for log in logs],
            'totals': totals,
            'goal': goal,
            'progress': {
                key: min(100.0, round(totals[key] / goal[key] * 100, 1))
                for key in goal
            },
        }

    @http_post('logs/', response={201: ExerciseLogOutputSchema})
    def create_log(self, request, payload: ExerciseLogInputSchema):
        exercise_type = None
        if payload.exercise_type_id:
            exercise_type = ExerciseType.objects.filter(
                id=payload.exercise_type_id).first()
            if not exercise_type:
                raise HttpError(404, "Exercise type not found")
        name = payload.name or (exercise_type.name if exercise_type else None)
        if not name:
            raise HttpError(400, "Either exercise_type_id or name is required")
        calories = payload.calories
        if not calories and exercise_type:
            calories = round(exercise_type.calories_per_minute * payload.minutes)
        log = ExerciseLog.objects.create(
            customer=request.user.customer,
            exercise_type=exercise_type,
            name=name,
            date=payload.date,
            minutes=payload.minutes,
            calories=calories,
            intensity=payload.intensity,
        )
        return 201, _exercise_log_out(log)

    @http_delete('logs/{log_id}/', response={200: SuccessSchema})
    def delete_log(self, request, log_id: int):
        deleted, _ = ExerciseLog.objects.filter(
            id=log_id, customer=request.user.customer).delete()
        if not deleted:
            raise HttpError(404, "Workout not found")
        return {"detail": {"title": "Deleted", "message": "Workout removed"}}


@api_controller("sleep/", tags=["Sleep"], permissions=[IsCustomer])
class SleepAPIController:
    """Nightly sleep log (one entry per date)."""

    @http_get('logs/', response=SleepLogListSchema)
    def list_logs(self, request, limit: int = 60):
        customer = request.user.customer
        limit = max(1, min(limit, 365))
        entries = list(SleepLog.objects.filter(customer=customer)[:limit])
        since = date_type.today() - timedelta(days=6)
        recent = [e for e in entries if e.date >= since]
        avg = (round(sum(float(e.duration_hours) for e in recent)
                     / len(recent), 1) if recent else None)
        return {
            'entries': entries,
            'stats': {
                'average_hours_7d': avg,
                'entries_7d': len(recent),
                'goal_hours': SLEEP_GOAL_HOURS,
            },
        }

    @http_post('logs/', response={200: SleepLogOutputSchema})
    def upsert_log(self, request, payload: SleepLogInputSchema):
        """Create the entry for `date`, or overwrite it if it exists."""
        log, _ = SleepLog.objects.update_or_create(
            customer=request.user.customer,
            date=payload.date,
            defaults={
                'duration_hours': round(payload.duration_hours, 1),
                'quality': payload.quality,
            },
        )
        log.refresh_from_db()
        return log

    @http_delete('logs/{log_id}/', response={200: SuccessSchema})
    def delete_log(self, request, log_id: int):
        deleted, _ = SleepLog.objects.filter(
            id=log_id, customer=request.user.customer).delete()
        if not deleted:
            raise HttpError(404, "Sleep entry not found")
        return {"detail": {"title": "Deleted", "message": "Sleep entry removed"}}
