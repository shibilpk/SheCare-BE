from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
import json
from django.urls import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic import TemplateView, View
from django.shortcuts import render
from core.decorators import role_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


class CheckRolesMixin(object):
    decorators = [login_required, role_required(['superuser'])]

    @method_decorator(decorators)
    def dispatch(self, request, *args, **kwargs):

        return super().dispatch(request, *args, **kwargs)


class App(CheckRolesMixin, View):
    def get(self, request):

        return HttpResponseRedirect(reverse('dashboard'))


class DashboardView(CheckRolesMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)



        context = {
            "title": "Dashboard",
            "is_dashboard": True,
        }
        return context


def page_not_found(request, exception=None):

    context = {
        "title": "Page Not Found",
        'message': "The page you are looking for does not exist.",
        'error_code': 404

    }
    return render(request, 'errors/404.html', context)


def error(request, exception=None):

    context = {
        "title": "Error",
        'message': "Some error occurred.",
        'error_code': 500

    }
    return render(request, 'errors/500.html', context)


def permission_denied(request, exception=None):

    context = {

        "title": "Permission Denied",
        'message': "You have no permission to do this action.",
        'error_code': 403

    }
    return render(request, 'errors/403.html', context)


def bad_request(request, exception=None):

    context = {
        "title": "Bad Request",
        'message': "Bad request. Please try again",
        'error_code': 400

    }
    return render(request, 'errors/400.html', context)
