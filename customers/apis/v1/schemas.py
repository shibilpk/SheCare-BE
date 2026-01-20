from ninja import Schema, Form, File
from pydantic import EmailStr, Field
from typing import Optional
from pydantic import field_validator
from ninja.files import UploadedFile
from datetime import date


class CustomerRegistrationSchema(Schema):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1)
    last_name: Optional[str] = None
    phone: Optional[str] = None


class CustomerRegistrationResponseSchema(Schema):
    state: int = 1
    message: str
    user_id: str


class TokenResponseSchema(Schema):
    state: int = 1
    access: str
    refresh: str
    user: dict


class ErrorResponseSchema(Schema):
    state: int = 0
    detail: str


class UserUpdateSchema(Schema):
    first_name: Optional[str] = Field(None, alias="user.first_name")
    last_name: Optional[str] = Field(None, alias="user.last_name")


class CustomerProfileSchema(Schema):
    email: str
    name: str
    phone: Optional[str] = None
    photo: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None


class CustomerProfileUpdateSchema(Schema):
    user: UserUpdateSchema = Field(..., alias="user")
    date_of_birth: Optional[date] = None
    height: Optional[float] = None


class CustomerProfileResponseSchema(Schema):
    state: int = 1
    profile: CustomerProfileSchema
