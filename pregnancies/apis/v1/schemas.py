from uuid import UUID
from ninja import Schema, ModelSchema, Field
from typing import List, Literal, Optional
from datetime import date, datetime, time as TimeOfDay
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


# ---------------------------------------------------------------- Appointments
class AppointmentInputSchema(Schema):
    title: str = Field(..., min_length=1, max_length=150)
    doctor: str = Field(default='', max_length=150)
    location: str = Field(default='', max_length=200)
    date: date
    time: Optional[TimeOfDay] = None
    notes: str = ''
    icon: str = Field(default='stethoscope', max_length=50)
    color: str = Field(default='#8B5CF6', max_length=7)
    is_completed: bool = False


class AppointmentOutputSchema(Schema):
    id: int
    title: str
    doctor: str
    location: str
    date: date
    time: Optional[TimeOfDay] = None
    notes: str
    icon: str
    color: str
    is_completed: bool


# ------------------------------------------------------------------- Checklist
class ChecklistItemOutputSchema(Schema):
    id: int
    label: str
    checked: bool
    is_custom: bool


class ChecklistCategorySchema(Schema):
    id: str
    label: str
    icon: str
    color: str
    items: List[ChecklistItemOutputSchema]


class ChecklistOutputSchema(Schema):
    categories: List[ChecklistCategorySchema]
    packed_count: int
    total_count: int


class ChecklistItemCreateSchema(Schema):
    label: str = Field(..., min_length=1, max_length=150)
    category: Literal['mom', 'baby', 'other'] = 'other'


class ChecklistItemUpdateSchema(Schema):
    checked: Optional[bool] = None
    label: Optional[str] = Field(default=None, min_length=1, max_length=150)


# ---------------------------------------------------------------- Child weight
class ChildWeightInputSchema(Schema):
    entry_date: date
    age_months: int = Field(..., ge=0, le=240)
    weight_kg: float = Field(..., gt=0, le=150)


class ChildWeightOutputSchema(Schema):
    id: int
    entry_date: date
    age_months: int
    age_label: str
    weight_kg: float
    gain_kg: float


# ------------------------------------------------------------------- Dashboard
class DashboardPregnancySchema(Schema):
    id: UUID
    due_date: date
    start_date: date
    baby_name: str
    current_week: int
    current_day: int
    trimester: int
    days_remaining: int
    total_weeks: int
    progress_percent: int


class DashboardBabySchema(Schema):
    week: int
    size_comparison: str
    length_cm: float
    weight_g: int
    development: str


class DashboardMaternalSchema(Schema):
    pre_pregnancy_weight_kg: Optional[float] = None
    current_weight_kg: Optional[float] = None
    weight_gain_kg: Optional[float] = None
    recommended_gain: str


class DashboardTodaySchema(Schema):
    water_glasses: float
    water_goal_glasses: int
    sleep_hours: Optional[float] = None
    exercise_minutes_week: int
    mood_ids: List[str]


class DashboardHealthMetricsSchema(Schema):
    nutrition: float
    hydration: float
    sleep: float
    exercise: float
    wellness: float


class WeekWeightSchema(Schema):
    week: int
    weight_kg: float


class WeekBabyWeightSchema(Schema):
    week: int
    weight_g: int


class DayActivitySchema(Schema):
    date: date
    label: str
    minutes: int


class WeekSymptomSchema(Schema):
    week: int
    count: int


class RecentSymptomSchema(Schema):
    id: str
    name: str
    days: int


class PregnancyDashboardSchema(Schema):
    pregnancy: DashboardPregnancySchema
    baby: DashboardBabySchema
    baby_growth: List[WeekBabyWeightSchema]
    maternal: DashboardMaternalSchema
    weight_series: List[WeekWeightSchema]
    today: DashboardTodaySchema
    health_metrics: DashboardHealthMetricsSchema
    activity_last_7_days: List[DayActivitySchema]
    symptoms_by_week: List[WeekSymptomSchema]
    recent_symptoms: List[RecentSymptomSchema]
    upcoming_appointment: Optional[AppointmentOutputSchema] = None
