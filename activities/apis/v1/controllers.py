from ninja_extra import api_controller, http_get, http_post

from activities.constants import (
    MOODS, RATING_SECTIONS, SYMPTOMS, ACTIVITIES,
    INTIMACY_OPTIONS, FLOW_OPTIONS)
from activities.apis.v1.schemas import (
    DailyEntryInputSchema, DailyEntryOutputSchema,
    HydrationLogInputSchema, HydrationLogOutputSchema,
    HydrationContentOutputSchema)
from core.models import DailyEntry
from activities.models import HydrationLog, HydrationContent


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
        daily_entry, created = DailyEntry.objects.update_or_create(
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
                intimacy_data = lookups['intimacy'].get(grouped['intimacy'][0].get('id'), {})
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
                flow_data = lookups['flow'].get(grouped['flow'][0].get('id'), {})
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
                avg_rating = sum(r.get('rating', 0) for r in daily_entry.ratings) / len(daily_entry.ratings)
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



