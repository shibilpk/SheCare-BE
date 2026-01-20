from django.contrib import admin

from .models import User

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password", "phone", "username")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    search_fields = ("email",)
    readonly_fields = ("last_login", "username")

    filter_horizontal = ("groups", "user_permissions")


admin.site.register(User, UserAdmin)
