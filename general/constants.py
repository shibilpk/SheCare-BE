from enum import Enum
from django.db import models


class OSType(models.TextChoices):
    IOS = "ios", "iOS"
    ANDROID = "android", "Android"


class OSTypeEnum(str, Enum):
    ios = OSType.IOS
    android = OSType.ANDROID
