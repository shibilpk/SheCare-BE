from accounts.apis.v1.permissions import IsCustomer
from ninja_extra import api_controller, http_get, http_post, http_put, paginate, route
from ninja.errors import HttpError
from ninja_extra.pagination import PageNumberPaginationExtra, PaginatedResponseSchema
from periods.models import Period
from periods.services import get_current_period_status
from datetime import datetime, timedelta
from django.utils import timezone
from .schemas import (
    CurrentPeriodSchema,
    PeriodDetailedOutSchema,
    PeriodInSchema,
    PeriodOutSchema,
    PeriodStartSchema,
    PeriodEndSchema,
)


@api_controller("period/", tags=["Period"], permissions=[IsCustomer])
class PeriodAPIController:

    @http_get(
        "active/",
        response={200: PeriodOutSchema},
    )
    def get_active_period(self, request):
        """
        Get active period entry for the authenticated customer
        """
        user = request.user
        customer = user.customer

        period_entry = Period.get_active_period(customer)

        if not period_entry:
            raise HttpError(404, "No active period entry found")
        return period_entry

    @http_post(
        "start/",
        response={200: PeriodOutSchema},
    )
    def create_period(self, request, data: PeriodInSchema):
        """
        Create a new period entry for the authenticated customer
        """
        user = request.user
        customer = user.customer
        period_entry = Period.objects.create(
            customer=customer,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        return period_entry

    @http_post(
        "end/",
        response={200: PeriodOutSchema},
    )
    def end_period(self, request, data: PeriodEndSchema):
        """
        Update an existing period by updating the start and/or end date
        """
        user = request.user
        customer = user.customer
        today = timezone.now()

        try:
            # Get the period that contains today's date
            period_entry = Period.objects.get(
                id=data.period_id,
                customer=customer,
                start_date__lte=today,
                end_date__gte=today
            )
        except Period.DoesNotExist:
            raise HttpError(404, "Active period not found")

        if data.start_date:
            period_entry.start_date = datetime.combine(
                data.start_date, datetime.min.time())
        period_entry.end_date = datetime.combine(
            data.end_date, datetime.min.time())
        period_entry.save()
        return period_entry

    @route.get(
        "list/",
        response={200: PaginatedResponseSchema[PeriodDetailedOutSchema]},
    )
    @paginate(PageNumberPaginationExtra, page_size=1)
    def get_period_list(self, request):
        """
        Get a list of all period entries for the authenticated customer
        """
        user = request.user
        customer = user.customer

        period_list = Period.objects.filter(
            customer=customer).order_by('-start_date')
        return period_list

    @route.get(
        "customer-data/",
        response={200: CurrentPeriodSchema, },
    )
    def get_customer_data(self, request):
        user = request.user
        customer = user.customer
        # profile = PeriodProfile.objects.filter(customer=customer).first()
        if hasattr(customer, 'period_profile'):
            profile = customer.period_profile
        else:
            raise HttpError(404, "No period profile found for customer")
        return get_current_period_status(profile)
