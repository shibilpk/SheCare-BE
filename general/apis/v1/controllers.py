from ninja.errors import HttpError
from ninja_extra import api_controller, http_get, http_post
from django.utils import timezone
import os
import json

from general.apis.v1.schemas import (
    AppVersionOutSchema,
    DailyTipSchema,
    StaticContentSchema,
    ContactUsInSchema,
    ContactUsOutSchema,
    FeedbackInSchema,
    FeedbackOutSchema,
    BlogPostSchema,
    HealthTipSchema,
)
from general.constants import OSTypeEnum, StaticContentTypeEnum
from typing import List
from general.models import (
    AppVersion, BlogPost, DailyTip, HealthTip, StaticContent, ContactUs,
    Feedback)


@api_controller('general/', tags=['General'])
class GeneralAPIController:
    """
    Authentication API Controller for user login, token management
    """

    @http_get(
        'app-version/{os_type}/',
        response={200: AppVersionOutSchema,
                  },
        auth=None
    )
    def app_version(self, request, os_type: OSTypeEnum):
        try:
            app_version = AppVersion.objects.filter(
                os=os_type.value).order_by('-release_date').first()
            if not app_version:
                raise HttpError(404, "App version not found")

            return {
                "version": app_version.version,
                "min_version": app_version.min_version,
                "release_date": app_version.release_date,
                "force_update": app_version.force_update,
                "download_url": app_version.download_url,
                "release_notes": list(app_version.release_notes.splitlines()),
            }
        except AppVersion.DoesNotExist:
            raise HttpError(404, "App version not found")

    @http_get(
        'health-tips/',
        response={200: List[HealthTipSchema]},
    )
    def health_tips(self, request):
        """General wellness tips (managed from the admin)."""
        return list(HealthTip.objects.filter(is_active=True))

    @http_get(
        'daily-tips/',
        response={200: DailyTipSchema,
                  404: dict},
    )
    def daily_tips(self, request):
        """
        Get today's daily tip for women's health and wellness
        """
        today = timezone.now().date()

        try:
            daily_tip = DailyTip.objects.get(date=today)
            return {
                "date": daily_tip.date,
                "short_description": daily_tip.short_description,
                "long_description": daily_tip.long_description,
            }
        except DailyTip.DoesNotExist:
            raise HttpError(
                404,
                "No daily tip available for today. "
                "Please run 'python manage.py populate_daily_tips' "
                "to generate tips."
            )

    @http_get(
        'animations/{animation_name}/',
        auth=None
    )
    def get_animation(self, request, animation_name: str):
        """
        Serve Lottie animation JSON files
        Supported animations: fireworks, devices
        """
        # Validate animation name (prevent directory traversal)
        allowed_animations = ['fireworks']
        if animation_name not in allowed_animations:
            raise HttpError(404, "Animation not found")

        # Build file path
        from django.conf import settings
        animation_path = os.path.join(
            settings.BASE_DIR,
            'staticfiles',
            'app',
            'animations',
            f'{animation_name}.json'
        )

        # Check if file exists
        if not os.path.exists(animation_path):
            raise HttpError(404, "Animation file not found")

        # Read and return JSON
        try:
            with open(animation_path, 'r') as f:
                animation_data = json.load(f)
            return animation_data
        except Exception as e:
            raise HttpError(500, f"Error loading animation: {str(e)}")


@api_controller('static-content/', tags=['Static Content'])
class StaticContentAPIController:
    """
    API Controller for static content (Privacy Policy, Terms of Service, Help & Support)
    """

    @http_get(
        '',
        response={200: list[StaticContentSchema]},
        auth=None
    )
    def list_static_content(self, request):
        """
        List all available static content
        """
        static_contents = StaticContent.objects.all()
        return [
            {
                "content_type": content.content_type,
                "content": json.loads(content.content) if isinstance(
                    content.content, str
                ) else content.content,
            }
            for content in static_contents
        ]

    @http_get(
        '{content_type}/',
        response={200: StaticContentSchema},
        auth=None
    )
    def get_static_content(self, request, content_type: StaticContentTypeEnum):
        """
        Fetch static content by type

        Args:
            content_type: One of 'privacy-policy', 'terms-of-service', 'help-support'

        Returns:
            Static content with EditorJS formatted content
        """
        try:
            static_content = StaticContent.objects.get(
                content_type=content_type.value
            )
            content_data = static_content.content
            # Parse JSON string to dict if needed
            if isinstance(content_data, str):
                content_data = json.loads(content_data)
            print(content_data)
            return {
                "content_type": static_content.content_type,
                "content": content_data,
            }
        except StaticContent.DoesNotExist:
            raise HttpError(404, "Static content not found")


@api_controller('blog/', tags=['Blog'])
class BlogAPIController:
    """
    API Controller for blog posts
    """

    @http_get(
        'posts/',
        response={200: dict},
        auth=None
    )
    def list_posts(self, request, page: int = 1, limit: int = 10):
        """
        List all blog posts ordered by published date with pagination

        Args:
            page: Page number (default: 1)
            limit: Number of posts per page (default: 10)
        """
        from django.core.paginator import Paginator

        posts = BlogPost.objects.all().order_by('-published_date')

        paginator = Paginator(posts, limit)
        page_obj = paginator.get_page(page)

        results = [
            {
                "id": post.id,
                "title": post.title,
                "short_description": post.short_description or "",
                "content": json.loads(post.content) if isinstance(
                    post.content, str
                ) else post.content,
                "author": post.author,
                "published_date": post.published_date,
                "created_at": post.created_at.date(),
            }
            for post in page_obj
        ]

        return {
            "count": paginator.count,
            "next": page_obj.next_page_number() if page_obj.has_next() else None,
            "previous": page_obj.previous_page_number() if page_obj.has_previous() else None,
            "results": results
        }

    @http_get(
        'posts/{post_id}/',
        response={200: BlogPostSchema},
        auth=None
    )
    def get_post(self, request, post_id: str):
        """
        Get a single blog post by ID
        """
        try:
            post = BlogPost.objects.get(id=post_id)
            content_data = post.content
            if isinstance(content_data, str):
                content_data = json.loads(content_data)

            return {
                "id": post.id,
                "title": post.title,
                "short_description": post.short_description or "",
                "content": content_data,
                "author": post.author,
                "published_date": post.published_date,
                "created_at": post.created_at.date(),
            }
        except BlogPost.DoesNotExist:
            raise HttpError(404, "Blog post not found")


@api_controller('contact-feedback/', tags=['Contact & Feedback'])
class ContactFeedbackAPIController:
    """
    API Controller for Contact Us and Feedback submissions
    """

    @http_post(
        'contact-us/',
        response={201: dict},
        auth=None
    )
    def submit_contact_us(self, request, payload: ContactUsInSchema):
        """
        Submit a contact us form
        """
        contact = ContactUs.objects.create(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            subject=payload.subject,
            message=payload.message
        )
        return {
            "success": True,
            "message": "Thank you for contacting us. We will get back to you soon!",
            "id": contact.id
        }

    @http_post(
        'feedback/',
        response={201: dict},
        auth=None
    )
    def submit_feedback(self, request, payload: FeedbackInSchema):
        """
        Submit a feedback form
        """
        # Validate rating
        if payload.rating < 1 or payload.rating > 5:
            raise HttpError(400, "Rating must be between 1 and 5")

        feedback = Feedback.objects.create(
            name=payload.name,
            email=payload.email,
            rating=payload.rating,
            feedback_type=payload.feedback_type,
            message=payload.message
        )
        return {
            "success": True,
            "message": "Thank you for your feedback! We appreciate your input.",
            "id": feedback.id
        }

    @http_get(
        'contact-us/',
        response={200: list[ContactUsOutSchema]}
    )
    def list_contact_us(self, request):
        """
        List all contact us submissions (admin only)
        """
        contacts = ContactUs.objects.all().order_by('-created_at')
        return [
            {
                "id": contact.id,
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "subject": contact.subject,
                "message": contact.message,
                "is_resolved": contact.is_resolved,
                "created_at": contact.created_at.date(),
            }
            for contact in contacts
        ]

    @http_get(
        'feedback/',
        response={200: list[FeedbackOutSchema]}
    )
    def list_feedback(self, request):
        """
        List all feedback submissions (admin only)
        """
        feedbacks = Feedback.objects.all().order_by('-created_at')
        return [
            {
                "id": fb.id,
                "name": fb.name,
                "email": fb.email,
                "rating": fb.rating,
                "feedback_type": fb.feedback_type,
                "message": fb.message,
                "is_reviewed": fb.is_reviewed,
                "created_at": fb.created_at.date(),
            }
            for fb in feedbacks
        ]
