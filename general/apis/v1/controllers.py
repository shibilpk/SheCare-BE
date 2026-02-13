from ninja.errors import HttpError
from ninja_extra import api_controller, http_get
from django.utils import timezone

from general.apis.v1.schemas import AppVersionOutSchema, DailyTipSchema
from general.constants import OSTypeEnum
from general.models import AppVersion, DailyTip


@api_controller('general/', tags=['General'])
class GeneralAPIController:
    """
    Authentication API Controller for user login, token management
    """

    @http_get(
        'app-version/{os_type}/',
        response={200: AppVersionOutSchema,
                  },
        auth=None
    )
    def app_version(self, request, os_type: OSTypeEnum):
        try:
            app_version = AppVersion.objects.filter(
                os=os_type.value).order_by('-release_date').first()
            if not app_version:
                raise HttpError(404, "App version not found")

            return {
                "version": app_version.version,
                "min_version": app_version.min_version,
                "release_date": app_version.release_date,
                "force_update": app_version.force_update,
                "download_url": app_version.download_url,
                "release_notes": list(app_version.release_notes.splitlines()),
            }
        except AppVersion.DoesNotExist:
            raise HttpError(404, "App version not found")

    @http_get(
        'daily-tips/',
        response={200: DailyTipSchema,
                  404: dict},
        auth=None
    )
    def daily_tips(self, request):
        """
        Get today's daily tip for women's health and wellness
        """
        today = timezone.now().date()

        try:
            daily_tip = DailyTip.objects.get(date=today)
            return {
                "date": daily_tip.date,
                "short_description": daily_tip.short_description,
                "long_description": daily_tip.long_description,
            }
        except DailyTip.DoesNotExist:
            raise HttpError(404, "No daily tip available for today. Please run 'python manage.py populate_daily_tips' to generate tips.")
