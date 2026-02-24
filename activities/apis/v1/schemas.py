from datetime import datetime, date
from ninja import Schema
from typing import List, Dict, Optional


class DailyDataItemSchema(Schema):
    id: str
    type: str  # 'mood', 'symptom', 'activity', 'flow', 'intimacy'


class DailyEntryInputSchema(Schema):
    date: date
    daily_data: List[DailyDataItemSchema] = []
    ratings: List[Dict] = []


class DailyEntryOutputSchema(Schema):
    id: int
    date: date
    daily_data: List[Dict]
    ratings: List[Dict]
    created_at: datetime
    updated_at: datetime


# Hydration Schemas
class HydrationLogInputSchema(Schema):
    date: date
    amount_ml: Optional[int] = 0
    glass_size_ml: Optional[int] = 250
    daily_goal_ml: Optional[int] = 2000


class HydrationLogOutputSchema(Schema):
    id: int
    date: date
    amount_ml: int
    glass_size_ml: int
    glasses_count: float
    daily_goal_ml: int
    total_liters: float
    progress_percent: float
    created_at: datetime
    updated_at: datetime


# Hydration Content Schemas
class HydrationContentItemSchema(Schema):
    id: int
    content_type: str
    icon: str
    text: str
    order: int


class HydrationContentOutputSchema(Schema):
    benefits: List[HydrationContentItemSchema]
    tips: List[HydrationContentItemSchema]


# Medication Schemas
class DoseScheduleSchema(Schema):
    dose_index: int
    time: str
    taken: bool


class MedicationInputSchema(Schema):
    name: str
    dosage: str
    frequency_period: str  # 'daily', 'weekly', 'monthly', 'once'
    times_per_period: int
    color: Optional[str] = '#EC4899'
    icon: Optional[str] = 'pharmacy'
    is_active: Optional[bool] = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class MedicationOutputSchema(Schema):
    id: int
    name: str
    dosage: str
    frequency_period: str
    times_per_period: int
    frequency_text: str
    color: str
    icon: str
    is_active: bool
    start_date: Optional[date]
    end_date: Optional[date]
    dose_times: List[str]
    created_at: datetime
    updated_at: datetime


class MedicationWithDosesOutputSchema(Schema):
    id: int
    name: str
    dosage: str
    frequency: str  # Human-readable frequency text
    icon: str
    color: str
    doses: List[DoseScheduleSchema]


class MedicationLogInputSchema(Schema):
    medication_id: int
    date: date
    dose_index: int
    taken: bool


class MedicationLogOutputSchema(Schema):
    id: int
    medication_id: int
    date: date
    dose_index: int
    dose_time: str
    taken: bool
    taken_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class MedicationStatsSchema(Schema):
    total_doses: int
    taken_doses: int
    completion_percent: float
