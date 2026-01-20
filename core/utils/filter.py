from django.http import QueryDict
from django.utils.datastructures import MultiValueDict

from django_filters import FilterSet, CharFilter
from django.forms.widgets import TextInput
from django.db.models import Q

from core.forms import BaseFormMethod


def has_key_startswith(key, dict_data, prefix=None):
    """
    Usage:
    >>> has_key_startswith('user', {'user__iexact': 'abcd'})
    >>> True
    """
    for _key, _values in dict_data.items():
        if len(_values) == 0:
            continue
        if _key.startswith(prefix + "-" + key if prefix else key):
            return True
    return False


def has_key_non_startswith(key, dict_data, prefix=None):
    """
    Usage:
    >>> has_key_startswith('user', {'user__iexact': ''})
    >>> True
    """
    for _key, _values in dict_data.items():
        if _key.startswith(prefix + "-" + key if prefix else key):
            return True
    return False


class FilterMixinNew:
    def get_saved_data(self):
        if self.request.user.is_authenticated:
            key = f"{self.__class__.__name__}-{self.request.user.pk}"

            session = self.request.session
            filter_data = session.get("saved_filter_data")
            if not filter_data:
                filter_data = session["saved_filter_data"] = {}

            return filter_data.get(key)

        return {}

    def _get_session_data(self):
        if self.request.user.is_authenticated:
            self.get_saved_data()

            clear_filter = self.data.get("clear_filter", None)
            if not clear_filter:
                if (
                    not any(
                        has_key_non_startswith(
                            field, self.data, self.form_prefix
                        )
                        for field in set(self.get_filters())
                    )
                    and self.get_saved_data()
                ):
                    data = self.get_saved_data()
                    query_dict = QueryDict("", mutable=True)
                    query_dict.update(MultiValueDict(data))
                    self.data = query_dict
        return self.data

    @property
    def form(self):
        if not hasattr(self, "_form"):
            Form = self.get_form_class()
            if self.is_bound:
                self._form = Form(
                    self._get_session_data(), prefix=self.form_prefix
                )
            else:
                self._form = Form(prefix=self.form_prefix)
        return self._form

    def _save_session_data(self):
        if self.request:
            session = self.request.session
            filter_data = session.get("saved_filter_data")

            if not filter_data:
                filter_data = session["saved_filter_data"] = {}

            if self.request.user.is_authenticated:
                key = f"{self.__class__.__name__}-{self.request.user.pk}"
                if self.data.get("filter_save_for_data"):
                    filter_data.update({key: dict(self.data)})
                    session.modified = True

                if self.data.get("filter_delete_for_data"):
                    if key in filter_data:
                        del filter_data[key]
                        session.modified = True

    hide_from_main = []

    @property
    def has_filter(self):
        self._save_session_data()
        return any(
            has_key_startswith(field, self.data, prefix=self.form_prefix)
            for field in set(self.get_filters()) - set(self.hide_from_main)
        )

