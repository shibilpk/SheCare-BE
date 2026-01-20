from django.conf import settings
from core.helpers import get_current_roles


def core_context(request):
    current_roles = get_current_roles(request.user)

    return {
        "app_title": "SheCare",
        "confirm_delete_message": "Are you sure want to delete this item. All associated data may be removed.",
        "revoke_access_message": "Are you sure to revoke this user's login access",
        "confirm_delete_selected_message": "Are you sure to delete all selected items.",
        "confirm_read_message": "Are you sure want to mark as read this item.",
        "confirm_read_selected_message": "Are you sure to mark as read all selected items.",
        "confirm_activate_message": "Do you want to activate this account",
        "confirm_deactivate_message": "Do you want to de-activate this account",
        "scheme": request.scheme,
        "host": request.get_host(),
        "current_roles": current_roles,
        "date_format": settings.SY_DATE_FORMATS['DISPLAY_DATE'],
        "time_format": settings.SY_DATE_FORMATS['DISPLAY_TIME'],
        "datetime_format": settings.SY_DATE_FORMATS['DISPLAY_DATETIME'],
    }
