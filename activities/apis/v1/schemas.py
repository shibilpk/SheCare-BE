from datetime import datetime, date
from ninja import Schema, ModelSchema, Field
from typing import List, Dict, Optional
from pydantic import validator
from activities.models import Medication, MedicationLog


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
    name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency_period: str  # 'daily', 'weekly', 'monthly', 'once'
    times_per_period: int = Field(..., ge=1, le=10)
    color: Optional[str] = Field(
        default='#EC4899',
        pattern=r'^#[0-9A-Fa-f]{6}$'
    )
    is_active: Optional[bool] = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @validator('frequency_period')
    def validate_frequency_period(cls, v):
        allowed = ['daily', 'weekly', 'monthly', 'once']
        if v not in allowed:
            raise ValueError(
                f'frequency_period must be one of: {", ".join(allowed)}'
            )
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class MedicationOutputSchema(ModelSchema):
    frequency_text: str
    dose_times: List[str]

    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'dosage', 'frequency_period', 'times_per_period',
            'color', 'is_active', 'start_date', 'end_date',
            'created_at', 'updated_at'
        ]


class MedicationWithDosesOutputSchema(Schema):
    id: int
    name: str
    dosage: str
    frequency: str  # Human-readable frequency text
    color: str
    doses: List[DoseScheduleSchema]


class MedicationLogInputSchema(Schema):
    medication_id: int = Field(..., gt=0)
    date: date
    dose_index: int = Field(..., ge=0)
    taken: bool


class MedicationLogOutputSchema(ModelSchema):
    medication_id: int

    class Meta:
        model = MedicationLog
        fields = [
            'id', 'date', 'dose_index', 'dose_time',
            'taken', 'taken_at', 'created_at', 'updated_at'
        ]


class MedicationStatsSchema(Schema):
    total_doses: int = Field(..., ge=0)
    taken_doses: int = Field(..., ge=0)
    completion_percent: float = Field(..., ge=0, le=100)


class ErrorResponseSchema(Schema):
    """Standard error response schema"""
    error: str
    detail: Optional[str] = None


# Nutrition Schemas
class NutritionLogInputSchema(Schema):
    date: date
    name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(default=100, ge=0)
    calories: int = Field(default=0, ge=0)
    carbs: float = Field(default=0, ge=0)
    protein: float = Field(default=0, ge=0)
    fat: float = Field(default=0, ge=0)


class NutritionLogOutputSchema(Schema):
    id: int
    date: date
    name: str
    quantity: int
    calories: int
    carbs: float
    protein: float
    fat: float
    created_at: datetime
    updated_at: datetime


class NutritionGoalInputSchema(Schema):
    calories: int = Field(default=2000, ge=0)
    carbs: float = Field(default=250, ge=0)
    protein: float = Field(default=75, ge=0)
    fat: float = Field(default=70, ge=0)


class NutritionGoalOutputSchema(Schema):
    id: int
    calories: int
    carbs: float
    protein: float
    fat: float
    created_at: datetime
    updated_at: datetime


class FoodSuggestionOutputSchema(Schema):
    id: int
    name: str
    calories: int
    carbs: float
    protein: float
    fat: float


class NutritionSummarySchema(Schema):
    date: date
    logs: List[NutritionLogOutputSchema]
    goal: NutritionGoalOutputSchema
    totals: Dict
    progress: Dict


class FoodSearchResultSchema(Schema):
    results: List[FoodSuggestionOutputSchema]
    total: int
    page: int
    page_size: int
    has_next: bool
