from ninja_extra import api_controller, http_get

from activities.constants import (
    MOODS, RATING_SECTIONS, SYMPTOMS, ACTIVITIES, INTIMACY_OPTIONS, FLOW_OPTIONS)


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
