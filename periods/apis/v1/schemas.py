from datetime import datetime, date
from uuid import UUID
from ninja import Schema
from ninja import ModelSchema

from periods.models import Period


class PeriodOutSchema(Schema):
    id: UUID
    start_date: datetime
    end_date: datetime


class PeriodInSchema(Schema):
    start_date: datetime
    end_date: datetime


class PeriodStartSchema(Schema):
    start_date: date
    end_date: date | None = None


class PeriodEndSchema(Schema):
    period_id: UUID
    start_date: date | None = None
    end_date: date


class PeriodDetailedOutSchema(Schema):
    id: UUID
    start_date: datetime
    end_date: datetime
    cycle_length: int | None


class CurrentPeriodSchema(Schema):
    active_period: PeriodDetailedOutSchema | None
    is_fertile: bool
    pregnancy_chance: str  # 'low', 'medium', or 'high'
    next_period_date: date | None
    ovulation_date: date | None
    fertile_window_start: date | None
    fertile_window_end: date | None
    avg_cycle_length: int | None
    avg_period_length: int | None
    late_period_days: int | None

    # Main card display data (server-calculated)
    card_status: str  # 'period_active', 'period_late', 'fertile_window', 'upcoming_ovulation', 'upcoming_period'
    card_label: str  # e.g., "Current Period", "Period Late", "Next Period"
    card_value: str  # e.g., "In Progress", "3 Days Late", "5 Days Left"
    card_subtitle: str  # e.g., "Jan 15 - Jan 20, 2026"
    card_button_text: str  # e.g., "End Period", "Start Period"
