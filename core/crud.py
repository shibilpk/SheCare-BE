import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.forms import formset_factory, inlineformset_factory
from django.forms.widgets import TextInput, FileInput
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.decorators import classonlymethod
from django_filters import CharFilter, FilterSet
from django.views.generic import View

from core.forms import BaseModeForm
from core.helpers import generate_form_errors, paginate, transform_string
from core.utils.filter import FilterMixinNew
from core.views import CheckRolesMixin
from asgiref.sync import markcoroutinefunction
from dal.autocomplete import Select2QuerySetView, ModelSelect2


class ViewSetMixin(LoginRequiredMixin, CheckRolesMixin, View):
    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):

        super().as_view(**initkwargs)
        # actions must not be empty

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            if "get" in actions and "head" not in actions:
                actions["head"] = actions["get"]

            # We also store the mapping of request methods to actions,
            # so that we can later set the action attribute.
            # eg. `self.action = 'list'` on an incoming GET request.
            self.action_map = actions

            # Bind methods to actions
            # This is the bit that's different to a standard view
            for method, action in actions.items():
                handler = getattr(self, action)
                setattr(self, method, handler)
            self.action = self.action_map.get(request.method.lower(), None)

            self.setup(request, *args, **kwargs)
            if not hasattr(self, "request"):
                raise AttributeError(
                    "%s instance has no 'request' attribute. Did you override "
                    "setup() and forget to call super()?" % cls.__name__
                )
            return self.dispatch(request, *args, **kwargs)

        view.view_class = cls
        view.view_initkwargs = initkwargs

        # __name__ and __qualname__ are intentionally left unchanged as
        # view_class should be used to robustly determine the name of the view
        # instead.
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.__annotations__ = cls.dispatch.__annotations__
        # Copy possible attributes set by decorators, e.g. @csrf_exempt, from
        # the dispatch method.
        view.__dict__.update(cls.dispatch.__dict__)

        # Mark the callback if the view class is async.
        if cls.view_is_async:
            markcoroutinefunction(view)

        return view


class CrudCreateView(View):
    create_title_msg = None
    create_message_msg = None
    redirect = None
    create_template_name = "crud/entry.html"
    model = None
    formsets = []
    form = None
    forms_auto_complete_fields = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.valid_formset_data = []
        self.formset_object = None
        self.data = None

    def get_dynamic_form(self, model):
        """
        Dynamically create a form for the model with all fields.
        """

        # Dynamically define a ModelForm subclass for the model

        class DynamicModelForm(BaseModeForm):
            class Meta:
                model = self.model
                exclude = ["is_deleted", "is_system_generated", "branch"]
                widgets = {
                    field: ModelSelect2(
                        url=(self.model._meta.get_field(field).
                             remote_field.model.get_autocomplete_url()),
                        attrs={'class': 'form-control',
                               'data-placeholder': f'Choose {field}',
                               'data-minimum-input-length': 0})
                    for field in self.forms_auto_complete_fields
                }

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for field_name, field in self.fields.items():
                    if isinstance(field.widget, FileInput):
                        existing_class = field.widget.attrs.get('class', '')
                        if 'custom-file-input' not in existing_class:
                            field.widget.attrs['class'] = (
                                existing_class + ' custom-file-input'
                            ).strip()

            def clean(self):
                cleaned_data = super().clean()
                return cleaned_data

        return DynamicModelForm

    @property
    def get_form(self):
        if self.form:
            return self.form
        return self.get_dynamic_form(self.model)

    def form_initial(self):
        return None

    def get_for_create_context_data(self, *args, **kwargs):
        form = self.get_form(initial=self.form_initial())
        formsets = self.get_for_create_formsets()
        context = {
            "form": form,
            "formsets": formsets,
            "title": "Create " + self.model._meta.verbose_name,
            "active_menu": (
                self.active_menu
                if self.active_menu
                else f"active-{transform_string(self.model.__name__)}"
            ),
            "instance_model": self.model,
        }
        return context

    def get_for_create_formsets(self):
        formset_data = []
        for form in self.formsets:
            formset = formset_factory(form, extra=1, can_delete_extra=True)
            if self.request.method == "POST":
                formset_data.append(
                    formset(
                        self.request.POST,
                        self.request.FILES,
                        prefix=f"{form.__name__.lower()}_formset",
                        form_kwargs={"empty_permitted": False},
                    )
                )
            else:
                formset_data.append(
                    formset(prefix=f"{form.__name__.lower()}_formset")
                )
        return formset_data

    def get_for_create(self, *args, **kwargs):
        context = self.get_for_create_context_data()
        return render(
            self.request,
            (
                f"{self.model.__name__.lower()}/entry.html"
                if not self.create_template_name
                else self.create_template_name
            ),
            context,
        )

    def do_post_save(self):
        return True

    def do_pre_form_save(self):
        return True

    def do_pre_formset_save(self):
        return True

    def extra_forms_to_validate(self):
        return []

    def get_redirect_url(self):
        redirect_url = self.data.get_list_url()
        next_url = self.request.GET.get("redirect_url")
        if next_url:
            redirect_url = next_url
        elif "_add_another" in self.request.POST:
            redirect_url = self.data.__class__.get_create_url()
        elif "_add_continue" in self.request.POST:
            redirect_url = self.data.get_update_url()
        elif "_add_view" in self.request.POST:
            redirect_url = self.data.get_absolute_url()
        return redirect_url

    def create(self, *args, **kwargs):
        form = self.get_form(self.request.POST, self.request.FILES)
        formsets = self.get_for_create_formsets()

        forms_to_validate = [form]
        forms_to_validate.extend(formsets)
        forms_to_validate.extend(self.extra_forms_to_validate())

        if all([form.is_valid() for form in forms_to_validate]):
            data = form.save(commit=False)
            self.data = data
            self.do_pre_form_save()
            data.save()
            form.save_m2m()

            for formset in formsets:
                for form in formset:
                    d_data = form.save(commit=False)
                    if hasattr(d_data, "is_active_object"):
                        if not d_data.is_active_object:
                            continue
                    setattr(d_data, form.get_fk_field(self.model)[0], data)
                    self.formset_object = d_data
                    self.do_pre_formset_save()
                    d_data.save()
                    self.valid_formset_data.append(d_data)
            self.do_post_save()

            title = (
                self.create_title_msg
                if self.create_title_msg
                else "Successfully Created"
            )
            message = (
                self.create_message_msg
                if self.create_message_msg
                else f"{self.model._meta.verbose_name} Successfully Created"
            )
            redirect = self.redirect if self.redirect else True
            response_data = {
                "status": True,
                "title": title,
                "message": message,
                "redirect": redirect,
                "redirect_url": self.get_redirect_url(),
            }

        else:
            message = str(generate_form_errors(form, formset=False))
            for form in formsets + self.extra_forms_to_validate():
                message += str(generate_form_errors(form, formset=True))
            response_data = {
                "status": False,
                "title": "Form validation error",
                "message": message,
            }

        return JsonResponse(response_data)

    def get(self, *args, **kwargs):
        return self.get_for_create()

    def post(self, *args, **kwargs):
        return self.create()


class CrudUpdateView(View):
    update_title_msg = None
    update_message_msg = None
    redirect = None
    update_template_name = "crud/entry.html"
    formsets = []
    model = None
    form = None

    def get_object(self, *args, **kwargs):
        pk = self.kwargs.get("pk")
        obj = self.model.objects.get(pk=pk)
        if getattr(obj, "is_system_generated", False):
            raise PermissionError("Cannot update system generated object")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.valid_formset_data = []
        self.formset_object = None
        self.data = None

    def get_dynamic_form(self, model):
        """
        Dynamically create a form for the model with all fields.
        """

        # Dynamically define a ModelForm subclass for the model
        class DynamicModelForm(BaseModeForm):
            class Meta:
                model = self.model
                exclude = ["is_deleted", "is_system_generated", "branch"]

            def clean(self):
                cleaned_data = super().clean()
                return cleaned_data

        return DynamicModelForm

    @property
    def get_form(self):
        if self.form:
            return self.form
        return self.get_dynamic_form(self.model)

    def form_initial(self):
        return None

    def get_for_update_context_data(self, *args, **kwargs):
        form = self.get_form(instance=self.object, initial=self.form_initial())
        formsets = self.get_for_update_formsets()
        context = {
            "form": form,
            "formsets": formsets,
            "title": "Update: " + self.object.__str__(),
            "instance": self.object,
            "redirect": True,
            "active_menu": (
                self.active_menu
                if self.active_menu
                else f"active-{transform_string(self.model.__name__)}"
            ),
        }
        return context

    def get_for_update_formsets(self):
        self.object = self.get_object()
        formset_data = []
        for form in self.formsets:
            formset = inlineformset_factory(
                self.model,
                form._meta.model,
                extra=1,
                form=form,
                can_delete=True,
            )
            if self.request.method == "POST":
                formset_data.append(
                    formset(
                        self.request.POST,
                        self.request.FILES,
                        instance=self.object,
                        prefix=f"{form.__name__.lower()}_formset",
                        form_kwargs={"empty_permitted": False},
                    )
                )
            else:
                formset_data.append(
                    formset(
                        instance=self.object,
                        prefix=f"{form.__name__.lower()}_formset",
                    )
                )
        return formset_data

    def do_post_save(self):
        return True

    def do_pre_form_save(self):
        return True

    def do_pre_formset_save(self):
        return True

    def do_pre_formset_delete(self):
        return True

    def extra_forms_to_validate(self):
        return []

    def get_redirect_url(self):
        redirect_url = self.object.get_list_url()
        next_url = self.request.GET.get("redirect_url")
        if next_url:
            redirect_url = next_url
        elif "_add_another" in self.request.POST:
            redirect_url = self.data.__class__.get_create_url()
        elif "_add_continue" in self.request.POST:
            redirect_url = self.data.get_update_url()
        elif "_add_view" in self.request.POST:
            redirect_url = self.data.get_absolute_url()
        return redirect_url

    def update(self, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(
            self.request.POST, self.request.FILES, instance=self.object
        )
        formsets = self.get_for_update_formsets()

        forms_to_validate = [form]
        forms_to_validate.extend(formsets)
        forms_to_validate.extend(self.extra_forms_to_validate())

        if all([form.is_valid() for form in forms_to_validate]):
            data = form.save(commit=False)
            self.data = data
            self.do_pre_form_save()
            data.save()
            form.save_m2m()

            for formset in formsets:
                for form in formset:
                    if form not in formset.deleted_forms:
                        d_data = form.save(commit=False)
                        d_data.form_initial = form.initial
                        if hasattr(d_data, "is_active_object"):
                            if not d_data.is_active_object:
                                d_data.delete()
                                continue
                        setattr(d_data, form.get_fk_field(self.model)[0], data)
                        self.formset_object = d_data
                        self.do_pre_formset_save()
                        d_data.save()
                        self.valid_formset_data.append(d_data)
                    else:
                        self.formset_object = form.instance
                        self.do_pre_formset_delete()
                        form.instance.delete()

            self.do_post_save()

            title = (
                self.update_title_msg
                if self.update_title_msg
                else "Successfully Updated"
            )
            message = (
                self.update_message_msg
                if self.update_message_msg
                else f"{self.model._meta.verbose_name} Successfully Updated"
            )
            redirect = self.redirect if self.redirect else True
            response_data = {
                "status": True,
                "title": title,
                "message": message,
                "redirect": redirect,
                "redirect_url": self.get_redirect_url(),
            }
        else:
            message = str(generate_form_errors(form, formset=False))
            for form in formsets + self.extra_forms_to_validate():
                message += str(generate_form_errors(form, formset=True))
            response_data = {
                "status": False,
                "stable": True,
                "title": "Form validation error",
                "message": message,
            }

        return JsonResponse(response_data)

    def get_for_update(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_for_update_context_data()
        return render(
            self.request,
            (
                f"{self.model.__name__.lower()}/entry.html"
                if not self.update_template_name
                else self.update_template_name
            ),
            context,
        )

    def get(self, *args, **kwargs):
        return self.get_for_update()

    def post(self, *args, **kwargs):
        return self.update()


class CrudListView(View):
    pagination_items = getattr(settings, "LIST_DEFAULT_PAGE_SIZE", 21)
    title = None
    list_template_name = "crud/list.html"
    list_display = ["__str__"]
    list_context_object_name = "instances"
    add_base_data = False
    model = None
    filter_conditions = None
    list_filter_class = None
    filter_search_fields = None
    active_menu = None

    def get_filter_search_fields(self):
        """
        Get the fields to search in.

        Returns:
            list: The fields to search in
        """
        if self.filter_search_fields is not None:
            return self.filter_search_fields

        # Dynamically find all CharField fields in the model
        filter_search_fields = []
        for field in self.model._meta.get_fields():
            # Check if field is a CharField or TextField
            if hasattr(field, "get_internal_type"):
                field_type = field.get_internal_type()
                if field_type in ("CharField", "TextField"):
                    filter_search_fields.append(field.name)

        return filter_search_fields

    def get_or_create_filter(self, qs):
        """
        Get or create a filter for the queryset.

        Args:
            qs (QuerySet): The queryset to filter

        Returns:
            FilterSet: The filter for the queryset
        """
        if self.list_filter_class:
            list_filter_class = self.list_filter_class
        else:

            class DefaultFilter(FilterMixinNew, FilterSet):
                filter_search_fields = self.get_filter_search_fields()
                hide_from_main = ["search"]
                search = CharFilter(
                    method="filter_search",
                    label="Search",
                    widget=TextInput(
                        attrs={
                            "placeholder": "Search here...",
                            "class": "form-control",
                            "id": None,
                        }
                    ),
                )

                def filter_search(self, queryset, name, value):
                    if not value:
                        return queryset

                    q_objects = Q()
                    for field in self.filter_search_fields:
                        q_objects |= Q(**{f"{field}__icontains": value})

                    return queryset.filter(q_objects)

                class Meta:
                    model = self.model
                    fields = ["search"]

            list_filter_class = DefaultFilter

        GET = self.request.GET.copy()
        return list_filter_class(GET, queryset=qs, request=self.request)

    def get_queryset(self):
        qs = self.model.objects.all()
        instances = qs.filter(is_deleted=False)
        if self.filter_conditions:
            instances = instances.filter(self.filter_conditions)

        return instances

    def get_for_list_context_data(self, *args, **kwargs):
        title = self.title if self.title else self.model._meta.verbose_name
        context = {}
        context["title"] = title
        context["active_menu"] = (
            self.active_menu
            if self.active_menu
            else f"active-{transform_string(self.model.__name__)}"
        )
        context["list_display"] = self.list_display
        context["add_base_data"] = self.add_base_data
        context["instance_model"] = self.model
        filtered_queryset = self.get_or_create_filter(self.get_queryset())
        instances, paginator = paginate(
            filtered_queryset.qs, self.request, self.pagination_items
        )
        context[self.list_context_object_name] = instances
        context["page_obj"] = paginator
        context["filter"] = filtered_queryset
        context["list_filter_class"] = self.list_filter_class

        return context

    def list(self, *args, **kwargs):
        context = self.get_for_list_context_data()
        return render(
            self.request,
            (
                f"{self.model.__name__.lower()}/list.html"
                if not self.list_template_name
                else self.list_template_name
            ),
            context,
        )

    def get(self, *args, **kwargs):
        return self.list()


class CrudRetrieveView(View):
    title = None
    retrieve_template_name = "crud/detail.html"
    retrieve_context_object_name = "instance"
    add_base_data = False
    detail_display = ["__str__"]
    formsets = []
    extra_html_to_render = []
    active_menu = None
    model = None

    def action_buttons(self):
        return []

    def get_object(self, *args, **kwargs):
        pk = self.kwargs.get("pk")
        try:
            obj = self.model.objects.get(pk=pk)
        except Exception:
            obj = None
        return obj

    def get_for_retrieve_context_data(self, *args, **kwargs):
        context = {}
        context["title"] = (
            self.title
            if self.title
            else self.model._meta.verbose_name + " - " + str(self.get_object())
        )
        context["active_menu"] = context["active_menu"] = (
            self.active_menu
            if self.active_menu
            else f"active-{transform_string(self.model.__name__)}"
        )
        context["detail_display"] = self.detail_display
        context["add_base_data"] = self.add_base_data
        context["formsets"] = self.formsets
        context["extra_html_to_render"] = self.extra_html_to_render
        context["action_buttons"] = self.action_buttons()
        context[self.retrieve_context_object_name] = self.get_object()
        return context

    def retrieve(self, *args, **kwargs):
        context = self.get_for_retrieve_context_data()
        return render(
            self.request,
            (
                f"{self.model.__name__.lower()}/retrieve.html"
                if not self.retrieve_template_name
                else self.retrieve_template_name
            ),
            context,
        )

    def get(self, *args, **kwargs):
        return self.retrieve()


class CrudDestroyView(View):
    destroy_title_msg = None
    destroy_message_msg = None
    redirect = None
    model = None

    def get_object(self, *args, **kwargs):
        pk = self.kwargs.get("pk")
        try:
            obj = self.model.objects.get(pk=pk)
        except Exception:
            obj = None
        return obj

    def destroy(self, *args, **kwargs):
        self.object = self.get_object()
        if getattr(self.object, "is_system_generated", False):
            response_data = {
                "status": False,
                "title": "Permission denied",
                "message": "Not Able to System Generated Item",
            }
        else:
            self.object.is_deleted = True
            self.object.save()

            title = (
                self.destroy_title_msg
                if self.destroy_title_msg
                else "Successfully Deleted"
            )
            message = (
                self.destroy_message_msg
                if self.destroy_message_msg
                else f"{self.model._meta.verbose_name} Successfully Deleted"
            )
            redirect = self.redirect if self.redirect else True
            response_data = {
                "status": True,
                "title": title,
                "message": message,
                "redirect": redirect,
                "redirect_url": self.object.get_list_url(),
            }
        return HttpResponse(
            json.dumps(response_data), content_type="application/javascript"
        )

    def get(self, *args, **kwargs):
        return self.destroy()


class CrudViewSet(
    CrudCreateView, CrudListView, CrudRetrieveView, CrudDestroyView,
    CrudUpdateView, ViewSetMixin
):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'model'):
            raise TypeError("Subclasses must define 'model' attribute")


class CrudAutoCompleteViewSet(
    CrudCreateView, CrudListView, CrudRetrieveView, CrudDestroyView,
    CrudUpdateView, Select2QuerySetView, ViewSetMixin
):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'model'):
            raise TypeError("Subclasses must define 'model' attribute")

    def get_for_autocomplete(self, *args, **kwargs):
        return super(Select2QuerySetView, self).get(*args, **kwargs)

    def post_for_autocomplete(self, *args, **kwargs):
        return super(Select2QuerySetView, self).post(*args, **kwargs)
