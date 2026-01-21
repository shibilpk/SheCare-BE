
from datetime import date
from ninja import Schema
from typing import List


class AppVersionOutSchema(Schema):
    version: str
    min_version: str
    release_date: date
    force_update: bool
    download_url: str
    release_notes: List[str]


class ErrorResponseSchema(Schema):
    detail: str
