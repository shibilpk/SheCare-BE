from decimal import Decimal
from ninja import Schema, ModelSchema
from pydantic import EmailStr, Field
from typing import List, Optional
from pydantic import field_validator
from datetime import date

from customers.constants import WeightUnisChoices, LanguageChoices, TimezoneChoices
from customers.models import WeightEntry, DiaryEntry
from general.apis.v1.schemas import DetailsSuccessSchema


# Using ModelSchema for WeightEntry
class WeightEntryOutSchema(ModelSchema):
    class Meta:
        model = WeightEntry
        fields = ['weight', 'unit']


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
    cycle_length: Optional[int] = None
    period_length: Optional[int] = None
    luteal_phase: Optional[int] = None


class CustomerProfileUpdateSchema(Schema):
    language: Optional[str] = None
    timezone: Optional[str] = None
    date_of_birth: Optional[date] = None
    height: Optional[Decimal] = Field(
        None,
        max_digits=5,
        decimal_places=2,
        ge=0
    )
    cycle_length: Optional[int] = Field(None, ge=20, le=45)
    period_length: Optional[int] = Field(None, ge=1, le=10)
    luteal_phase: Optional[int] = Field(None, ge=10, le=18)

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
        ge=0
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


# Using ModelSchema for DiaryEntry
class CustomerDiaryEntryInOutSchema(ModelSchema):
    class Meta:
        model = DiaryEntry
        fields = ['entry_date', 'content']


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


class ReminderSettingsSchema(Schema):
    reminder_settings: list


class ReminderSettingsUpdateSchema(Schema):
    reminder_settings: list


class ReminderSettingsResponseSchema(Schema):
    reminder_settings: list
    detail: DetailsSuccessSchema


class ReminderUpdateResponseSchema(Schema):
    reminder: dict
    detail: DetailsSuccessSchema


class ReminderInfoSchema(Schema):
    reminder_info: List[str]
