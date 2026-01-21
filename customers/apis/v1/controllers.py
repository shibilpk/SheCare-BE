from typing import Optional
from ninja.files import UploadedFile
from django.db import transaction
from accounts.apis.v1.permissions import IsCustomer
from accounts.models import User, UserOtp
from core.helpers import encrypt_small
from customers.models import Customer
from django.contrib.auth import get_user_model
from ninja_extra import api_controller, http_post, http_get, http_patch
from ninja import Form, File, Body
from ninja_jwt.tokens import RefreshToken
from ninja.errors import HttpError
from .schemas import (
    CustomerProfileUpdateSchema,
    CustomerRegistrationResponseSchema,
    CustomerRegistrationSchema,
    TokenResponseSchema,
    ErrorResponseSchema,
    CustomerProfileResponseSchema
)


@api_controller('customer/', tags=['Customer'])
class CustomerAPIController:
    """
    Customer API Controller for profile management
    """

    @http_post(
        'register/',
        response={200: CustomerRegistrationResponseSchema,
                  400: ErrorResponseSchema},
        auth=None,
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
                user.last_name = payload.last_name
                user.username = email
            else:
                # Create new inactive user
                user = User(
                    email=email,
                    username=email,
                    first_name=payload.first_name,
                    last_name=payload.last_name,
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
            "message": "Registration successful. Please verify your email to activate your account.",
            "user_id": encrypt_small(user.id)
        }



    @http_get(
        'profile/',
        response={200: CustomerProfileResponseSchema,
                  401: ErrorResponseSchema, 404: ErrorResponseSchema},
        permissions=[IsCustomer]

    )
    def get_profile(self, request):
        """
        Get authenticated customer profile details
        """
        user = request.user
        customer = user.customer
        return {
            "profile": customer.get_profile_data(request)
        }

    @http_patch(
        'profile/',
        response={200: CustomerProfileResponseSchema,
                  401: ErrorResponseSchema, 400: ErrorResponseSchema}
    )
    def profile_update(
        self, request, payload: CustomerProfileUpdateSchema = Form(...),
        photo: Optional[UploadedFile] = File(None)
    ):
        """
        Update authenticated customer profile
        """
        user = request.user
        customer = user.customer
        customer_dict = payload.dict(exclude_unset=True)
        user_dict = customer_dict.pop('user')
        if user_dict:
            for key, value in user_dict.items():
                setattr(user, key, value)
            user.save(update_fields=user_dict.keys())

        if photo is not None:
            customer_dict['photo'] = photo

        if customer_dict:
            for key, value in customer_dict.items():
                setattr(customer, key, value)
            customer.save(update_fields=customer_dict.keys())

        return {
            "profile": customer.get_profile_data(request)
        }
