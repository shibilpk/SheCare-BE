from typing import ClassVar
from ninja import Schema
from pydantic import EmailStr, Field
from ninja import Schema
from pydantic import EmailStr, model_validator, ValidationError
from ninja.errors import HttpError


class CustomMessageStr400Mixin:
    # Define as a class variable that subclasses can override
    _LOGIN_ERROR_MESSAGES: ClassVar[dict] = {}

    @model_validator(mode='wrap')
    @classmethod
    def validate_login_fields(cls, data, handler):
        try:
            # Try to validate the data normally
            return handler(data)
        except ValidationError as e:
            errors = {}
            # Catch the error and find which field is missing
            for error in e.errors():
                if error['type'] == 'missing':
                    field_name = error['loc'][-1]
                    # Use custom message if available, otherwise default
                    errors[field_name] = [
                        cls._LOGIN_ERROR_MESSAGES.get('missing', {}).get(
                            field_name, 'This field is required')]
            if errors:
                raise HttpError(400, errors)
            else:
                # If it's not a 'missing' error, just raise the original error
                raise e


class LoginSchema(Schema, CustomMessageStr400Mixin):
    email: EmailStr
    password: str

    # Custom error messages for LoginSchema
    _LOGIN_ERROR_MESSAGES: ClassVar[dict] = {
        'missing': {
            'email': 'Email is required.',
            'password': 'Password is required.'
        }
    }


class EmailSchema(Schema, CustomMessageStr400Mixin):
    email: EmailStr
    # Custom error messages for EmailSchema
    _LOGIN_ERROR_MESSAGES: ClassVar[dict] = {
        'missing': {
            'email': 'Email is required.'
        }
    }


class TokenResponseSchema(Schema):
    access: str
    refresh: str
    user: dict


class RefreshTokenSchema(Schema):
    refresh: str = Field(
        ...,
        min_length=1,
        description="Refresh token",
        json_schema_extra={
            "error_messages": {
                "required": "Refresh token is required.",
                "min_length": "Refresh token cannot be empty."
            }
        }
    )


class RefreshTokenResponseSchema(Schema):
    access: str
    refresh: str


class VerifyTokenResponseSchema(Schema):
    valid: bool

class UserExistsResponseSchema(Schema):
    exists: bool

class ErrorResponseSchema(Schema):
    detail: str


class VerifyOTPSchema(Schema):
    otp: str = Field(..., min_length=4, max_length=6)
    # is_registration defaults to False
    is_login: bool = False
