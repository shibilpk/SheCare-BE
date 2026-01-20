from django import forms


class BaseFormMethod:
    def _add_base_styling(self, field):
        """Add base Bootstrap form-control class to all fields."""
        field.widget.attrs['class'] = self._merge_classes(
            field.widget.attrs.get('class'),
            'form-control'
        )

    def _handle_required_attribute(self, field):
        """Explicitly handle required fields and add visual indicators."""
        if field.required:
            field.widget.attrs['required'] = 'required'
            field.widget.attrs['class'] = self._merge_classes(
                field.widget.attrs.get('class'),
                'required-field'
            )

    def _add_placeholder(self, field):
        """Add placeholder text if not already specified."""
        if 'placeholder' not in field.widget.attrs:
            try:
                field.widget.attrs['placeholder'] = (
                    f"Enter {field.label}" if field.label
                    else f"Enter {field.name.replace('_', ' ').title()}"
                )
            except Exception:
                pass

    def _handle_textarea_fields(self, field):
        """Special handling for textarea fields."""
        if isinstance(field.widget, forms.Textarea):
            field.widget.attrs['rows'] = 3
            field.widget.attrs['class'] = self._merge_classes(
                field.widget.attrs.get('class'),
                'textarea-field'
            )

    def _apply_widget_customizations(self, is_filter=False):
        """Apply any widget-specific customizations defined in the Widget class.

        Args:
            is_filter (bool): Whether the fields are filter fields, which require
                accessing the underlying field through the .field attribute.
        """
        widget = getattr(self, "Widget", None)
        if not widget:
            return

        # Helper function to get the appropriate field attribute
        def get_field_attr(field_name):
            field = self.fields[field_name]
            return field.field if is_filter else field

        # Handle class additions
        for field_name, classes in getattr(widget, "classes", {}).items():
            if field_name in self.fields:
                field_attr = get_field_attr(field_name)
                current_class = field_attr.widget.attrs.get('class', '')
                field_attr.widget.attrs['class'] = self._merge_classes(
                    current_class, classes)

        # Handle attribute additions
        for field_name, attrs in getattr(widget, "attr", {}).items():
            if field_name in self.fields:
                field_attr = get_field_attr(field_name)
                field_attr.widget.attrs.update(attrs)

    @staticmethod
    def _merge_classes(existing_classes, new_classes):
        """Helper method to merge CSS classes without duplicates."""
        if not existing_classes:
            return new_classes

        existing = set(existing_classes.split())
        new = set(new_classes.split())
        return ' '.join(existing | new)


class BaseModeForm(BaseFormMethod, forms.ModelForm):
    """Base model form with automatic Bootstrap styling and enhanced attributes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            self._add_base_styling(field)
            self._handle_required_attribute(field)
            self._add_placeholder(field)
            self._handle_textarea_fields(field)

        self._apply_widget_customizations()

    @classmethod
    def get_fk_field(cls, model):
        """
        Returns the name(s) of the field(s) in the form's model that have a
        ForeignKey to the passed model.
        """
        fk_field_name = None
        for field in cls._meta.model._meta.get_fields():
            if field.is_relation and field.related_model == model:
                fk_field_name = field.name
                related_name = getattr(field, "related_name", None)
                if not related_name:
                    related_name = f"{cls._meta.model.__name__.lower()}_set"

                return fk_field_name, related_name
        if not fk_field_name:
            raise ValueError("No ForeignKey field found in form")
