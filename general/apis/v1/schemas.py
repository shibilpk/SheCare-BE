
from datetime import date
from ninja import Schema
from typing import List


class DetailsSuccessSchema(Schema):
    title: str
    message: str


class ErrorSchema(Schema):
    detail: DetailsSuccessSchema


class SuccessSchema(Schema):
    detail: DetailsSuccessSchema


class AppVersionOutSchema(Schema):
    version: str
    min_version: str
    release_date: date
    force_update: bool
    download_url: str
    release_notes: List[str]


class DailyTipSchema(Schema):
    date: date
    short_description: str
    long_description: str
