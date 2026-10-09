from ninja import Schema, ModelSchema
from typing import List, Optional

from general.models import AppVersion, DailyTip, StaticContent, ContactUs, Feedback, BlogPost


class DetailsSuccessSchema(Schema):
    title: str
    message: str


class ErrorSchema(Schema):
    detail: DetailsSuccessSchema


class SuccessSchema(Schema):
    detail: DetailsSuccessSchema


# Using ModelSchema for AppVersion
class AppVersionOutSchema(ModelSchema):
    release_notes: List[str]

    class Meta:
        model = AppVersion
        fields = ['version', 'min_version', 'release_date', 'force_update', 'download_url']


# Using ModelSchema for DailyTip
class DailyTipSchema(ModelSchema):
    class Meta:
        model = DailyTip
        fields = ['date', 'short_description', 'long_description']


# Using ModelSchema for StaticContent
class StaticContentSchema(ModelSchema):
    class Meta:
        model = StaticContent
        fields = ['content_type', 'content']


class ContactUsInSchema(Schema):
    name: str
    email: str
    phone: str = ""
    subject: str
    message: str


# Using ModelSchema for ContactUs output
class ContactUsOutSchema(ModelSchema):
    class Meta:
        model = ContactUs
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'is_resolved', 'created_at']


class FeedbackInSchema(Schema):
    name: str
    email: str
    rating: int
    feedback_type: str = "general"
    message: str


# Using ModelSchema for Feedback output
class FeedbackOutSchema(ModelSchema):
    class Meta:
        model = Feedback
        fields = ['id', 'name', 'email', 'rating', 'feedback_type', 'message', 'is_reviewed', 'created_at']


# Using ModelSchema for BlogPost
class BlogPostSchema(ModelSchema):
    short_description: Optional[str] = None

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'short_description', 'content', 'author', 'published_date', 'created_at']
