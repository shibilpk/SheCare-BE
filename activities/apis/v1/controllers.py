from ninja_extra import (
    api_controller, http_get, http_post, http_put, http_delete
)
from typing import List
from django.db.models import Q, Sum

from activities.constants import (
    MOODS, RATING_SECTIONS, SYMPTOMS, ACTIVITIES,
    INTIMACY_OPTIONS, FLOW_OPTIONS)
from activities.apis.v1.schemas import (
    DailyEntryInputSchema, DailyEntryOutputSchema,
    HydrationLogInputSchema, HydrationLogOutputSchema,
    HydrationContentOutputSchema,
    MedicationInputSchema, MedicationOutputSchema,
    MedicationWithDosesOutputSchema, MedicationLogInputSchema,
    MedicationLogOutputSchema, MedicationStatsSchema,
    ErrorResponseSchema,
    NutritionLogInputSchema, NutritionLogOutputSchema,
    NutritionGoalInputSchema, NutritionGoalOutputSchema,
    FoodSuggestionOutputSchema, NutritionSummarySchema,
    FoodSearchResultSchema)
from core.models import DailyEntry
from activities.models import (
    HydrationLog, HydrationContent,
    NutritionLog, NutritionGoal, FoodSuggestion)
from activities.services import MedicationService


@api_controller("activities/", tags=["Daily Actions"])
class ActivitiesAPIController:
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
        user = request.user

        # Transform daily_data to list of dicts
        daily_data_list = [
            {"id": item.id, "type": item.type}
            for item in payload.daily_data
        ]

        # Get or create the daily entry for this date
        daily_entry, _ = DailyEntry.objects.update_or_create(
            user=user,
            date=payload.date,
            defaults={
                'daily_data': daily_data_list,
                'ratings': payload.ratings,
            }
        )

        return daily_entry

    @http_get('daily-entries/{date}',
              response={200: DailyEntryOutputSchema, 404: dict})
    def get_daily_entry(self, request, date: str):
        """Get daily entry for a specific date"""
        user = request.user

        try:
            daily_entry = DailyEntry.objects.get(user=user, date=date)
            return 200, daily_entry
        except DailyEntry.DoesNotExist:
            return 404, {"detail": "No entry found for this date"}

    @http_get('daily-entries-detailed/{date}',
              response={200: dict, 404: dict})
    def get_daily_entries_detailed(self, request, date: str):
        """Get daily entry summary for a specific date"""
        user = request.user

        try:
            daily_entry = DailyEntry.objects.get(user=user, date=date)

            # Group data by type
            grouped = {
                'mood': [],
                'symptom': [],
                'activity': [],
                'intimacy': [],
                'flow': [],
            }

            for item in daily_entry.daily_data:
                item_type = item.get('type')
                if item_type in grouped:
                    grouped[item_type].append(item)

            # Create lookup dictionaries
            lookups = {
                'mood': {item['id']: item for item in MOODS},
                'symptom': {item['id']: item for item in SYMPTOMS},
                'activity': {item['id']: item for item in ACTIVITIES},
                'intimacy': {item['id']: item for item in INTIMACY_OPTIONS},
                'flow': {item['id']: item for item in FLOW_OPTIONS},
            }

            # Build summary cards
            summary_cards = []
            card_id = 1

            # Moods summary
            if grouped['mood']:
                mood_names = []
                for item in grouped['mood']:
                    mood_data = lookups['mood'].get(item.get('id'), {})
                    if mood_data.get('emoji'):
                        mood_names.append(mood_data['emoji'])

                summary_cards.append({
                    'id': card_id,
                    'icon': '😊',
                    'title': f"{len(grouped['mood'])} Mood{'s' if len(grouped['mood']) > 1 else ''} Added",
                    'value': ' '.join(mood_names[:5]),  # Show first 5 emojis
                    'color': '#FFE0B2',
                })
                card_id += 1

            # Symptoms summary
            if grouped['symptom']:
                summary_cards.append({
                    'id': card_id,
                    'icon': 'thermometer',
                    'title': f"{len(grouped['symptom'])} Symptom{'s' if len(grouped['symptom']) > 1 else ''} Tracked",
                    'value': f"{len(grouped['symptom'])} logged",
                    'color': '#FFCDD2',
                })
                card_id += 1

            # Activities summary
            if grouped['activity']:
                activity_emojis = []
                for item in grouped['activity']:
                    activity_data = lookups['activity'].get(item.get('id'), {})
                    if activity_data.get('emoji'):
                        activity_emojis.append(activity_data['emoji'])

                summary_cards.append({
                    'id': card_id,
                    'icon': '💪',
                    'title': f"{len(grouped['activity'])} Activit{'ies' if len(grouped['activity']) > 1 else 'y'}",
                    'value': ' '.join(activity_emojis[:5]),
                    'color': '#C8E6C9',
                })
                card_id += 1

            # Intimacy summary
            if grouped['intimacy']:
                intimacy_data = lookups['intimacy'].get(
                    grouped['intimacy'][0].get('id'), {})
                summary_cards.append({
                    'id': card_id,
                    'icon': intimacy_data.get('emoji', '❤️'),
                    'title': 'Intimacy',
                    'value': intimacy_data.get('label', 'Logged'),
                    'color': intimacy_data.get('color', '#F8BBD0'),
                })
                card_id += 1

            # Flow summary
            if grouped['flow']:
                flow_data = lookups['flow'].get(
                    grouped['flow'][0].get('id'), {})
                summary_cards.append({
                    'id': card_id,
                    'icon': flow_data.get('emoji', '💧'),
                    'title': 'Flow',
                    'value': flow_data.get('label', 'Logged'),
                    'color': flow_data.get('color', '#E1F5FE'),
                })
                card_id += 1

            # Ratings summary
            if daily_entry.ratings:
                avg_rating = sum(r.get('rating', 0)
                                 for r in daily_entry.ratings) / len(daily_entry.ratings)
                summary_cards.append({
                    'id': card_id,
                    'icon': 'star',
                    'title': f"{len(daily_entry.ratings)} Rating{'s' if len(daily_entry.ratings) > 1 else ''}",
                    'rating': round(avg_rating, 1),
                    'color': '#FFF9C4',
                })
                card_id += 1

            return 200, {
                'id': daily_entry.id,
                'date': str(daily_entry.date),
                'summary_cards': summary_cards,
                'created_at': daily_entry.created_at.isoformat(),
                'updated_at': daily_entry.updated_at.isoformat(),
            }
        except DailyEntry.DoesNotExist:
            return 404, {"detail": "No entry found for this date"}


@api_controller("hydration/", tags=["Hydration"])
class HydrationAPIController:

    # Hydration Endpoints
    @http_get(
        'hydration/{date}',
        response={200: HydrationLogOutputSchema, 404: dict}
    )
    def get_hydration_log(self, request, date: str):
        """Get hydration log for a specific date"""
        user = request.user

        try:
            hydration_log = HydrationLog.objects.get(
                user=user, date=date
            )
            return 200, hydration_log
        except HydrationLog.DoesNotExist:
            return 404, {"detail": "No hydration log found for this date"}

    @http_post('hydration/', response=HydrationLogOutputSchema)
    def create_or_update_hydration_log(
            self, request, payload: HydrationLogInputSchema):
        """Create or update hydration log for a specific date"""
        user = request.user

        hydration_log, created = HydrationLog.objects.get_or_create(
            user=user,
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
        'medications/by-date/{date}',
        response=List[MedicationWithDosesOutputSchema]
    )
    def get_medications_with_doses(self, request, date: str):
        """Get all medications with their dose status for a specific date"""
        medications_with_doses = self.service.get_medications_with_doses(
            user=request.user,
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
            user=request.user,
            medication_data=medication_data
        )
        return 201, medication

    @http_put(
        'medications/{medication_id}',
        response={
            200: MedicationOutputSchema,
            404: ErrorResponseSchema,
            400: ErrorResponseSchema
        }
    )
    def update_medication(
        self, request, medication_id: int, payload: MedicationInputSchema
    ):
        """Update an existing medication asdasdas asdasds asdasda asdasd asdsadas sadasdas asdsa """
        medication = self.service.get_medication_by_id(
            medication_id, request.user
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
        'medications/{medication_id}',
        response={200: dict, 404: ErrorResponseSchema}
    )
    def delete_medication(self, request, medication_id: int):
        """Soft delete a medication by marking it as inactive"""
        medication = self.service.get_medication_by_id(
            medication_id, request.user
        )

        if not medication:
            return 404, {
                "error": self.MEDICATION_NOT_FOUND,
                "detail": f"No medication found with ID {medication_id}"
            }

        self.service.soft_delete_medication(medication)
        return 200, {
            "message": "Medication deleted successfully",
            "medication_id": medication_id
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
            request.user
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

    @http_get('medication-stats/{date}', response=MedicationStatsSchema)
    def get_medication_stats(self, request, date: str):
        """Get medication completion statistics for a specific date"""
        stats = self.service.get_medication_stats(
            user=request.user,
            target_date=date
        )
        return stats


@api_controller("nutrition/", tags=["Nutrition"])
class NutritionAPIController:
    """Controller for nutrition tracking endpoints"""

    @http_get(
        'summary/{date}',
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
        'logs/{log_id}',
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
        'logs/{log_id}',
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
