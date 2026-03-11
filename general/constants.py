from enum import Enum
from django.db import models


class OSType(models.TextChoices):
    IOS = "ios", "iOS"
    ANDROID = "android", "Android"


class OSTypeEnum(str, Enum):
    ios = OSType.IOS
    android = OSType.ANDROID


class LanguageChoice(models.TextChoices):
    ENGLISH = 'en', 'English'
    MALAYALAM = 'ml', 'Malayalam'


class StaticContentType(models.TextChoices):
    PRIVACY_POLICY = 'privacy-policy', 'Privacy Policy'
    TERMS_OF_SERVICE = 'terms-of-service', 'Terms of Service'
    HELP_SUPPORT = 'help-support', 'Help and Support'


class StaticContentTypeEnum(str, Enum):
    PRIVACY_POLICY = StaticContentType.PRIVACY_POLICY
    TERMS_OF_SERVICE = StaticContentType.TERMS_OF_SERVICE
    HELP_SUPPORT = StaticContentType.HELP_SUPPORT
