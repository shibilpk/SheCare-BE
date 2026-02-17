from datetime import datetime, date
from ninja import Schema
from typing import List, Dict


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
