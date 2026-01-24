from django.utils.translation import gettext_lazy as _
import itertools
from django.apps import apps
from django.contrib import admin
from django.db import models

class ListAdminMixin(object):
    def __init__(self, model, admin_site):
        fields = [
            field.name for field in model._meta.fields if not field.many_to_many]
        self.list_display = [
            name for name in itertools.chain(fields, ['__str__'])]
        self.list_display_links = [
            name for name in itertools.chain(fields[:7], ['__str__'])]
        self.search_fields = [
            field.name for field in model._meta.get_fields() if not field.is_relation]

        # Additional features
        self.list_filter = [
            field.name for field in model._meta.fields
            if isinstance(field, (models.BooleanField, models.DateField, models.DateTimeField))
            or (isinstance(field, models.ForeignKey) and field.choices)
            or (isinstance(field, models.CharField) and field.choices)
        ]
        self.date_hierarchy = 'created_at' if 'created_at' in fields else None
        self.ordering = ['-created_at'] if 'created_at' in fields else []

        super(ListAdminMixin, self).__init__(model, admin_site)

all_models = apps.get_models()
registered_models = admin.site._registry

for model in all_models:
    if model not in registered_models:
        admin_class = type(
            'AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
        admin.site.register(model, admin_class)