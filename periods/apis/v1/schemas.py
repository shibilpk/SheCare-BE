from datetime import datetime
from ninja import Schema
from ninja import ModelSchema

from periods.models import Period


class PeriodOutSchema(Schema):
    start_date: datetime
    end_date: datetime


class PeriodInSchema(Schema):
    start_date: datetime
    end_date: datetime


class PeriodDetailedOutSchema(Schema):
    start_date: datetime
    end_date: datetime
    cycle_length: int | None
    is_active: bool
