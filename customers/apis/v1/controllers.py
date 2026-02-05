from datetime import date
from typing import Optional
from ninja.files import UploadedFile
from django.db import transaction
from accounts.apis.v1.permissions import IsCustomer
from accounts.models import User, UserOtp
from core.helpers import encrypt_small
from customers.models import Customer, CustomerDiaryEntry, WeightEntry
from ninja_extra import api_controller, http_post, http_get, http_patch
from ninja import Form, File
from ninja.errors import HttpError

from general.apis.v1.schemas import DetailsSuccessSchema, SuccessSchema
from .schemas import (
    CustomerDiaryEntryInOutSchema,
    CustomerProfileUpdateOutSchema,
    CustomerProfileUpdateSchema,
    CustomerRegistrationResponseSchema,
    CustomerRegistrationSchema,
    CustomerProfileResponseSchema,
    HealthAnalysisResponseSchema,
    WeightEntryInSchema,
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
            customer, _ = Customer.objects.get_or_create(user=user)
            UserOtp.create_email_otp(user.email)

        return 200, {
            "detail": {
                "title": "Success",
                "message": "Please check your email to verify your account",
            },
            "user_id": encrypt_small(user.id),
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
        user_dict = customer_dict.pop("user")
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
