from django.contrib.auth import authenticate, get_user_model
from ninja_extra import api_controller, http_post
from ninja_jwt.tokens import RefreshToken
from ninja.errors import HttpError, ValidationError
from django.conf import settings
from ninja import Form

from accounts.models import User, UserOtp
from core.helpers import decrypt_small
from .schemas import (
    EmailSchema,
    LoginSchema,
    RefreshTokenSchema,
    TokenResponseSchema,
    RefreshTokenResponseSchema,
    VerifyTokenResponseSchema,
    ErrorResponseSchema,
    VerifyOTPSchema,
)


@api_controller('auth/', tags=['Authentication'])
class AuthAPIController:
    """
    Authentication API Controller for user login, token management
    """

    @http_post(
        'login/',
        response={200: TokenResponseSchema,
                  400: ErrorResponseSchema, 401: ErrorResponseSchema},
        auth=None
    )
    def login(self, request, payload: LoginSchema):
        """
        User login endpoint
        Returns access and refresh tokens if credentials are valid
        Accepts both JSON and form data
        """
        # Authenticate user
        user = authenticate(
            request,
            username=payload.email,
            password=payload.password
        )

        if user is None:
            raise HttpError(401, "Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise HttpError(401, "User account is disabled")

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": str(user.phone) if user.phone else None,
        }

        # Add customer_id if customer profile exists
        if hasattr(user, 'customer'):
            user_data["customer_id"] = user.customer.id

        return {
            "state": 1,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_data
        }

    @http_post(
        'verify-otp/{str:user_id}/',
        response={200: TokenResponseSchema,
                  400: ErrorResponseSchema, 401: ErrorResponseSchema},
        auth=None
    )
    def verify_otp(self, request, user_id: str, payload: VerifyOTPSchema):
        """
        Verify OTP for user login
        Validates OTP from UserOtp model and returns tokens if valid
        """
        try:
            # Get the user by ID
            is_login = payload.is_login
            user = User.objects.get(
                id=decrypt_small(user_id), is_active=is_login)
        except User.DoesNotExist:
            raise HttpError(400, "User with this ID does not exist")

        # Get the active OTP for this user
        try:
            user_otp = UserOtp.objects.get(
                email=user.email,
                is_active=True
            )
        except UserOtp.DoesNotExist:
            raise HttpError(400, "No active OTP found for this user")

        # Verify the OTP
        if user_otp.otp != payload.otp:
            user_otp.failed_attempts += 1
            user_otp.save()

            if user_otp.failed_attempts >= 3:
                user_otp.is_active = False
                user_otp.save()
                raise HttpError(
                    400, "Maximum OTP verification attempts exceeded")

            raise HttpError(400, "Invalid OTP")

        # OTP is valid, mark it as inactive
        user_otp.is_active = False
        user_otp.save()

        if is_login:
            # Ensure user is active for login
            if not user.is_active:
                raise HttpError(401, "User account is disabled")
        else:
            # For registration, activate the user
            user.is_active = True
            user.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": str(user.phone) if user.phone else None,
        }

        # Add customer_id if customer profile exists
        if hasattr(user, 'customer'):
            user_data["customer_id"] = user.customer.id

        return {
            "state": 1,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_data
        }

    @http_post(
        'refresh/',
        response={200: RefreshTokenResponseSchema, 401: ErrorResponseSchema},
        auth=None
    )
    def refresh_token(self, request, payload: RefreshTokenSchema):
        """
        Refresh access token using refresh token
        When ROTATE_REFRESH_TOKENS is True, returns a new refresh token
        """
        try:
            # Validate the old refresh token
            refresh = RefreshToken(payload.refresh)

            if settings.NINJA_JWT.get('ROTATE_REFRESH_TOKENS', False):
                # Create a completely new refresh token for rotation
                # Get the user from the token
                user_id = refresh.get('user_id')
                user = User.objects.get(id=user_id)
                refresh = RefreshToken.for_user(user)

            return {
                "state": 1,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        except User.DoesNotExist:
            raise HttpError(401, "User not found")
        except Exception as e:
            raise HttpError(401, "Invalid or expired refresh token")

    @http_post(
        'verify-token/',
        response={200: VerifyTokenResponseSchema, 401: ErrorResponseSchema},
        auth=None
    )
    def verify_token(self, request, token: str):
        """
        Verify if access token is valid
        """
        from ninja_jwt.tokens import AccessToken

        try:
            AccessToken(token)
            return {"state": 1, "valid": True}
        except Exception:
            raise HttpError(401, "Invalid or expired token")

    @http_post(
        'check-user/',
        response={400: ErrorResponseSchema, 401: ErrorResponseSchema},
        auth=None
    )
    def check_user(self, request, payload: EmailSchema):
        """
        User login endpoint
        Returns access and refresh tokens if credentials are valid
        Accepts both JSON and form data
        """
        try:
            User.objects.get(email=payload.email, is_active=True)
        except User.DoesNotExist:
            raise HttpError(400, "User with this email does not exist")
        return {
            "state": 1,
            "otp_login_allowed": True
        }
