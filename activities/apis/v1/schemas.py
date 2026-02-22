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
