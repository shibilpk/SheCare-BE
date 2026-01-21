from ninja.errors import HttpError
from ninja_extra import api_controller, http_get

from general.apis.v1.schemas import AppVersionOutSchema, ErrorResponseSchema
from general.constants import OSTypeEnum
from general.models import AppVersion


@api_controller('general/', tags=['General'])
class GeneralAPIController:
    """
    Authentication API Controller for user login, token management
    """

    @http_get(
        'app-version/{os_type}/',
        response={200: AppVersionOutSchema,
                  400: ErrorResponseSchema, 401: ErrorResponseSchema},
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
