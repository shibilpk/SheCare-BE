
from datetime import date
from ninja import Schema
from typing import List
from uuid import UUID


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


class StaticContentSchema(Schema):
    content_type: str
    content: dict


class ContactUsInSchema(Schema):
    name: str
    email: str
    phone: str = ""
    subject: str
    message: str


class ContactUsOutSchema(Schema):
    id: UUID
    name: str
    email: str
    phone: str
    subject: str
    message: str
    is_resolved: bool
    created_at: date


class FeedbackInSchema(Schema):
    name: str
    email: str
    rating: int
    feedback_type: str = "general"
    message: str


class FeedbackOutSchema(Schema):
    id: UUID
    name: str
    email: str
    rating: int
    feedback_type: str
    message: str
    is_reviewed: bool
    created_at: date


class BlogPostSchema(Schema):
    id: UUID
    title: str
    short_description: str = None
    content: dict
    author: str
    published_date: date
    created_at: date
