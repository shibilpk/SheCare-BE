from ninja import Schema, ModelSchema
from typing import Optional
from datetime import date, datetime
from pregnancies.models import Pregnancy


class PregnancyInputSchema(Schema):
    due_date: Optional[date] = None
    baby_name: Optional[str] = ""
    doctor_name: Optional[str] = ""
    hospital_name: Optional[str] = ""


class PregnancyUpdateSchema(Schema):
    due_date: Optional[date] = None
    last_period_date: Optional[date] = None
    baby_name: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None


class PregnancyOutputSchema(ModelSchema):
    last_period_date: Optional[date]
    weeks_pregnant: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Meta:
        model = Pregnancy
        fields = [
            'id', 'due_date', 'baby_name', 'doctor_name', 'hospital_name',
            'is_active', 'baby_born', 'pregnancy_lost', 'mistaken_toggle'
        ]


class BabyBornSchema(Schema):
    child_name: str
    birth_date: date
    birth_weight: Optional[float] = None
    birth_length: Optional[float] = None
    child_gender: Optional[str] = ""


class PregnancyEndSchema(Schema):
    reason: str  # 'born', 'lost', 'mistake'
    baby_details: Optional[BabyBornSchema] = None


class PregnancyStatusSchema(Schema):
    has_active_pregnancy: bool
    pregnancy: Optional[PregnancyOutputSchema] = None


class SuccessMessageSchema(Schema):
    title: str
    message: str
