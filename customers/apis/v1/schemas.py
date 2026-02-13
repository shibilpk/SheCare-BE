from decimal import Decimal
from ninja import Schema, Form, File
from pydantic import EmailStr, Field, StrictFloat
from typing import List, Optional, Annotated
from pydantic import field_validator
from ninja.files import UploadedFile
from datetime import date
from pydantic import condecimal

from customers.constants import WeightUnisChoices, LanguageChoices, TimezoneChoices
from general.apis.v1.schemas import DetailsSuccessSchema


class WeightEntryOutSchema(Schema):
    weight: Decimal
    unit: str


class CustomerRegistrationSchema(Schema):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1)
    phone: Optional[str] = None


class CustomerRegistrationResponseSchema(Schema):
    detail: DetailsSuccessSchema
    user_id: str


class TokenResponseSchema(Schema):
    access: str
    refresh: str
    user: dict


class UserUpdateSchema(Schema):
    first_name: Optional[str] = Field(None, alias="user.first_name")


class CustomerProfileSchema(Schema):
    email: str
    name: str
    phone: Optional[str] = None
    photo: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[WeightEntryOutSchema] = None
    date_of_birth: Optional[date] = None
    language: str = LanguageChoices.ENGLISH
    timezone: str = TimezoneChoices.ASIA_KOLKATA


class CustomerProfileUpdateSchema(Schema):
    language: Optional[str] = None
    timezone: Optional[str] = None
    height: Optional[Decimal] = Field(
        None,
        max_digits=5,
        decimal_places=2,
        ge=0  # 'ge' means Greater than or Equal to 0
    )

    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v is not None and v not in LanguageChoices.values:
            raise ValueError(f"language must be one of {LanguageChoices.values}")
        return v

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        if v is not None and v not in TimezoneChoices.values:
            raise ValueError(f"timezone must be one of {TimezoneChoices.values}")
        return v

    # @field_validator("height")
    # def height_must_be_real(cls, v):
    #     if v is not None and (v != v):  # NaN check
    #         raise ValueError("height must be a valid number")
    #     return v

    @field_validator('height', mode='before')
    @classmethod
    def allow_empty_string_as_none(cls, v):
        if v == "":
            return None
        return v


class CustomerProfileResponseSchema(Schema):
    profile: CustomerProfileSchema


class CustomerProfileUpdateOutSchema(Schema):
    profile: CustomerProfileSchema
    detail: DetailsSuccessSchema


class WeightEntryInSchema(Schema):
    weight: Decimal = Field(
        ...,
        max_digits=5,
        decimal_places=2,
        ge=0  # 'ge' means Greater than or Equal to 0
    )
    weight_date: date
    weight_unit: str

    @field_validator('weight_unit')
    @classmethod
    def validate_units(cls, v):
        valid_units = WeightUnisChoices.values
        if v not in valid_units:
            raise ValueError(f"units must be one of {valid_units}")
        return v


class BmiHealthSummaryOutSchema(Schema):
    bmi: float
    notes: List[str]
    new_bmi: float
    status: str
    status_badge_color: str


class HealthAnalysisResponseSchema(Schema):
    bmi: Optional[BmiHealthSummaryOutSchema] = None
    profile: Optional[CustomerProfileSchema] = None


class CustomerDiaryEntryInOutSchema(Schema):
    entry_date: date
    content: str


class PreferencesUpdateSchema(Schema):
    language: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v is not None and v not in LanguageChoices.values:
            raise ValueError(f"language must be one of {LanguageChoices.values}")
        return v

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        if v is not None and v not in TimezoneChoices.values:
            raise ValueError(f"timezone must be one of {TimezoneChoices.values}")
        return v


class LanguageOptionSchema(Schema):
    value: str
    label: str


class TimezoneOptionSchema(Schema):
    value: str
    label: str


class PreferencesOptionsSchema(Schema):
    languages: List[LanguageOptionSchema]
    timezones: List[TimezoneOptionSchema]
