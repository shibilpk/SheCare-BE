import uuid
from django.db import IntegrityError, models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.conf import settings

from core.helpers import transform_string
from core.middlewares import RequestMiddleware


class ActiveManager(models.Manager):
    def get_queryset(self):
        return (
            super(ActiveManager, self).get_queryset().exclude(is_deleted=True)
        )


class CrudUrlMixin:

    @property
    def url_base_name(self):
        return transform_string(self.__class__.__name__)

    @classmethod
    def get_list_url(cls):
        url_base_name = transform_string(cls.__name__)
        return reverse(f"{cls._meta.app_label}:list-{url_base_name}")

    @classmethod
    def get_create_url(cls):
        url_base_name = transform_string(cls.__name__)
        return reverse(f"{cls._meta.app_label}:create-{url_base_name}")

    def get_absolute_url(self, auto_id=False):
        return reverse(
            f"{self._meta.app_label}:retrieve-{self.url_base_name}",
            args=[self.pk],
        )

    def get_update_url(self):
        return reverse(
            f"{self._meta.app_label}:update-{self.url_base_name}",
            args=[self.pk]
        )

    def get_destroy_url(self):
        return reverse(
            f"{self._meta.app_label}:destroy-{self.url_base_name}",
            args=[self.pk],
        )

    @classmethod
    def get_autocomplete_url(cls):
        url_base_name = transform_string(cls.__name__)
        return reverse(f"{cls._meta.app_label}:autocomplete-{url_base_name}")


class BaseModel(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        editable=False,
        related_name="creator_%(app_label)s_%(class)s_objects",
        limit_choices_to={"is_active": True},
        on_delete=models.CASCADE,
    )
    updater = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        editable=False,
        related_name="updater_%(app_label)s_%(class)s_objects",
        limit_choices_to={"is_active": True},
        on_delete=models.CASCADE,
    )
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(null=True, blank=True, editable=False)
    is_deleted = models.BooleanField(default=False, editable=False)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        abstract = True
        ordering = ("-id",)

    def base_data(self, request):
        if self._state.adding:
            if request.user.is_authenticated:
                self.creator = request.user
        else:
            if request.user.is_authenticated:
                self.updater = request.user
            self.date_updated = timezone.now()

    def save(self, request=None, *args, **kwargs):
        request = RequestMiddleware(get_response=None)
        if request := getattr(request.thread_local, "current_request", None):
            self.base_data(request)
        super().save(*args, **kwargs)

    @classmethod
    def get_abstract_fields(cls):
        # Return a list of field names from the abstract model
        return [field.name for field in cls._meta.fields]

    def delete(self, hard=False):
        if hard:
            super(BaseModel, self).delete()
        else:
            self.is_deleted = True
            self.save()


class UUIDBaseModel(BaseModel):
    id = models.UUIDField(
        primary_key=True, editable=False, db_index=True
    )
    auto_id = models.AutoField(editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ("-auto_id",)

    def save(self, request=None, *args, **kwargs):
        if self._state.adding:
            uid = uuid.uuid4()
            try:
                self.uid = uid
            except IntegrityError:
                uid = uuid.uuid4()
                self.uid = uid
        super().save(*args, **kwargs)


class RelatedModal(models.Model):
    is_deleted = models.BooleanField(default=False, editable=False)

    class Meta:
        abstract = True


class Mode(models.Model):
    readonly = models.BooleanField(default=False)
    maintenance = models.BooleanField(default=False)
    down = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Mode")
        verbose_name_plural = _("Mode")
        ordering = ("id",)

    class Admin:
        list_display = ("id", "readonly", "maintenance", "down")

    def __str__(self):
        return str(self.id)
