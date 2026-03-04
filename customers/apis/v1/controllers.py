from datetime import date
from typing import Optional
from ninja.files import UploadedFile
from django.db import transaction
from accounts.apis.v1.permissions import IsCustomer
from accounts.models import User, UserOtp
from core.helpers import encrypt_small
from customers.models import Customer, CustomerDiaryEntry, WeightEntry, Reminder
from customers.constants import (
    LanguageChoices,
    TimezoneChoices,
    DEFAULT_REMINDER_CHOICES,
)
from ninja_extra import api_controller, http_post, http_get, http_patch
from ninja import Form, File
from ninja.errors import HttpError

from general.apis.v1.schemas import SuccessSchema
from .schemas import (
    CustomerDiaryEntryInOutSchema,
    CustomerProfileUpdateOutSchema,
    CustomerProfileUpdateSchema,
    CustomerRegistrationResponseSchema,
    CustomerRegistrationSchema,
    CustomerProfileResponseSchema,
    HealthAnalysisResponseSchema,
    ReminderInfoSchema,
    WeightEntryInSchema,
    PreferencesUpdateSchema,
    PreferencesOptionsSchema,
    ReminderSettingsSchema,
    ReminderSettingsUpdateSchema,
    ReminderUpdateResponseSchema,
)


@api_controller("customer/", tags=["Customer"], auth=None)
class CustomerOpenAPIController:
    """
    Customer API Controller for profile management
    """

    @http_post(
        "register/",
        response={200: CustomerRegistrationResponseSchema},
    )
    def register(self, request, payload: CustomerRegistrationSchema):
        """
        Customer registration endpoint
        Allows re-registration if user exists but is inactive
        """

        email = payload.email.lower().strip()

        with transaction.atomic():
            user = User.objects.filter(email=email).first()

            if user and user.is_active:
                raise HttpError(400, "User with this email already exists")

            if user:
                # User exists but is inactive → replace data
                user.first_name = payload.first_name
                user.username = email
            else:
                # Create new inactive user
                user = User(
                    email=email,
                    username=email,
                    first_name=payload.first_name,
                    is_active=False,
                )

            user.set_password(payload.password)

            if payload.phone:
                user.phone = payload.phone

            user.is_active = False
            user.save()

            # Create customer profile only if it does not exist
            _, _ = Customer.objects.get_or_create(user=user)
            UserOtp.create_email_otp(user.email)

        return 200, {
            "detail": {
                "title": "Success",
                "message": "Please check your email to verify your account",
            },
            "user_id": encrypt_small(user.id),
        }

    @http_get(
        "preferences/options/",
        response={200: PreferencesOptionsSchema},
        auth=None,
    )
    def get_preferences_options(self, request):
        """
        Get available language and timezone options
        """
        languages = [
            {"value": choice[0], "label": choice[1]}
            for choice in LanguageChoices.choices
        ]
        timezones = [
            {"value": choice[0], "label": choice[1]}
            for choice in TimezoneChoices.choices
        ]

        return {
            "languages": languages,
            "timezones": timezones,
        }


@api_controller("customer/", tags=["Customer"], permissions=[IsCustomer])
class CustomerAPIController:
    """
    Customer API Controller for profile management
    """

    @http_get(
        "profile/",
        response={
            200: CustomerProfileResponseSchema,
        },
    )
    def get_profile(self, request):
        """
        Get authenticated customer profile details
        """
        user = request.user
        customer = user.customer
        return {"profile": customer.get_profile_data(request)}

    @http_patch(
        "profile/",
        response={
            200: CustomerProfileUpdateOutSchema,
        },
    )
    def profile_update(
        self,
        request,
        payload: CustomerProfileUpdateSchema = Form(...),
        photo: Optional[UploadedFile] = File(None),
    ):
        """
        Update authenticated customer profile
        """
        user = request.user
        customer = user.customer
        customer_dict = payload.dict(exclude_unset=True)
        user_dict = customer_dict.pop("user", {})
        if user_dict:
            for key, value in user_dict.items():
                setattr(user, key, value)
            user.save(update_fields=user_dict.keys())

        if photo is not None:
            customer_dict["photo"] = photo

        if customer_dict:
            for key, value in customer_dict.items():
                setattr(customer, key, value)
            customer.save(update_fields=customer_dict.keys())

        return {
            "profile": customer.get_profile_data(request),
            "detail": {
                "title": "Success",
                "message": "Profile updated successfully",
            },
        }

    @http_patch(
        "profile/wight-entry/",
        response={
            200: CustomerProfileUpdateOutSchema,
        },
    )
    def weight_entry(self, request, payload: WeightEntryInSchema = Form(...)):
        """
        Update authenticated customer profile
        """
        user = request.user
        customer = user.customer

        WeightEntry.objects.create(
            customer=customer,
            weight=payload.weight,
            entry_date=payload.weight_date,
            unit=payload.weight_unit,
        )

        return {
            "profile": customer.get_profile_data(request),
            "detail": {
                "title": "Success",
                "message": "Profile updated successfully",
            },
        }

    @http_get(
        "health-analysis/",
        response={
            200: HealthAnalysisResponseSchema,
        },
    )
    def get_health_analysis(self, request):
        """
        Get authenticated customer profile details
        """
        user = request.user
        customer = user.customer
        return {
            "bmi": customer.get_bmi_data(),
            "profile": customer.get_profile_data(request),
        }

    @http_patch(
        "preferences/",
        response={200: CustomerProfileUpdateOutSchema},
    )
    def update_preferences(self, request, payload: PreferencesUpdateSchema):
        """
        Update language and timezone preferences
        """
        user = request.user
        customer = user.customer

        update_fields = []

        if payload.language is not None:
            customer.language = payload.language
            update_fields.append("language")

        if payload.timezone is not None:
            customer.timezone = payload.timezone
            update_fields.append("timezone")

        if update_fields:
            customer.save(update_fields=update_fields)

        return {
            "profile": customer.get_profile_data(request),
            "detail": {
                "title": "Success",
                "message": "Preferences updated successfully",
            },
        }


@api_controller("reminder/", tags=["Reminder"], permissions=[IsCustomer])
class CustomerReminderAPIController:

    @http_get(
        "reminder-info/",
        response={200: ReminderInfoSchema},
    )
    def get_reminder_info(self, request):
        """
        Get reminder info for the authenticated customer
        """
        return {
            "reminder_info": [
                'Enable period reminders to get notified about your upcoming cycle.',
                'Use ovulation reminders to track your fertile window.',
                'Set medication reminders to never miss a dose.',
                'Customize reminder times and advance days to fit your schedule.',
            ]
        }

    @http_get(
        "reminder-settings/",
        response={200: ReminderSettingsSchema},
    )
    def get_reminder_settings(self, request):
        """
        Get reminder settings for the authenticated customer
        Returns default reminders merged with user's saved customizations
        """
        user = request.user
        customer = user.customer

        # Get user's saved reminders
        saved_reminders = {
            reminder.reminder_type: reminder
            for reminder in customer.reminders.all()
        }

        # Merge defaults with saved reminders
        reminder_list = []
        for default_reminder in DEFAULT_REMINDER_CHOICES:
            reminder_type = default_reminder['reminder_type']
            saved = saved_reminders.get(reminder_type)

            reminder_list.append({
                "reminder_type": reminder_type,
                "title": default_reminder['title'],
                "icon": default_reminder.get('icon'),
                "color": default_reminder.get('color', '#666'),
                "enabled": saved.enabled if saved else default_reminder['enabled'],
                "time": saved.time if saved else default_reminder['time'],
                "days_advance": saved.days_advance if saved else default_reminder['days_advance'],
            })

        return {
            "reminder_settings": reminder_list
        }

    @http_patch(
        "reminder-settings/",
        response={200: ReminderUpdateResponseSchema},
    )
    def update_reminder_settings(self, request, payload: ReminderSettingsUpdateSchema):
        """
        Update reminder settings for the authenticated customer
        Returns only the updated reminder
        """
        user = request.user
        customer = user.customer

        # Create a map of defaults for quick lookup
        defaults_map = {
            default['reminder_type']: default
            for default in DEFAULT_REMINDER_CHOICES
        }

        # We expect only one reminder in the update
        if not payload.reminder_settings or len(payload.reminder_settings) == 0:
            raise HttpError(400, "No reminder data provided")

        reminder_data = payload.reminder_settings[0]
        reminder_type = reminder_data['reminder_type']
        default = defaults_map.get(reminder_type)

        if not default:
            raise HttpError(400, "Invalid reminder type")

        # Get values from request or default
        is_enabled = reminder_data.get('enabled', default['enabled'])
        time = reminder_data.get('time', default['time'])
        days_advance = reminder_data.get(
            'days_advance', default['days_advance'])

        # Save the reminder
        Reminder.objects.update_or_create(
            customer=customer,
            reminder_type=reminder_type,
            defaults={
                'enabled': is_enabled,
                'time': time,
                'days_advance': days_advance,
            }
        )

        # Return the updated reminder
        return {
            "reminder": {
                "reminder_type": reminder_type,
                "title": default['title'],
                "icon": default.get('icon', 'bell'),
                "color": default.get('color', '#666'),
                "enabled": is_enabled,
                "time": time,
                "days_advance": days_advance,
            },
            "detail": {
                "title": "Success",
                "message": "Reminder updated successfully",
            },
        }


@api_controller("diary/", tags=["Diary"], permissions=[IsCustomer])
class CustomerDiaryAPIController:

    @http_post(
        "entry/",
        response={200: SuccessSchema},
    )
    def add_diary_entry(self, request, payload: CustomerDiaryEntryInOutSchema):
        """
        Add a diary weight entry for the authenticated customer
        """
        user = request.user
        customer = user.customer

        _, created = CustomerDiaryEntry.objects.update_or_create(
            customer=customer,
            entry_date=payload.entry_date,
            defaults={"content": payload.content},

        )
        if not created:
            message = "Diary entry updated successfully"
        else:
            message = "Diary entry added successfully"
        return {
            "detail": {
                "title": "Success",
                "message": message
            }
        }

    @http_get(
        "entry-by-date/",
        response={200: CustomerDiaryEntryInOutSchema},
    )
    def get_diary_entry_by_date(self, request, entry_date: date):
        """
        Get a diary weight entry for the authenticated customer by date
        """
        user = request.user
        customer = user.customer

        diary_entry = CustomerDiaryEntry.objects.filter(
            customer=customer,
            entry_date=entry_date
        ).first()

        if not diary_entry:
            raise HttpError(404, "Diary entry not found for the given date")

        return {
            "entry_date": diary_entry.entry_date,
            "content": diary_entry.content
        }
