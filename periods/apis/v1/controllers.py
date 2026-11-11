from accounts.apis.v1.permissions import IsCustomer
from uuid import UUID
from ninja_extra import (
    api_controller, http_get, http_post, http_put, http_delete, paginate, route)
from ninja.errors import HttpError
from ninja_extra.pagination import PageNumberPaginationExtra, PaginatedResponseSchema
from periods.models import Period
from periods.services import get_current_period_status
from datetime import datetime, timedelta
from general.apis.v1.schemas import SuccessSchema
from django.utils import timezone
from .schemas import (
    CurrentPeriodSchema,
    PeriodDetailedOutSchema,
    PeriodInSchema,
    PeriodOutSchema,
    PeriodStartSchema,
    PeriodEndSchema,
    PeriodUpdateSchema,
    PregnancyChanceSchema,
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

    @route.get(
        "pregnancy-chance/",
        response={200: PregnancyChanceSchema, },
    )
    def get_pregnancy_chance(self, request):
        """
        Get pregnancy chance with percentage for the authenticated customer
        Returns level (low/medium/high) and percentage (0-100)
        """
        user = request.user
        customer = user.customer
        if hasattr(customer, 'period_profile'):
            profile = customer.period_profile
        else:
            raise HttpError(404, "No period profile found for customer")

        # Get pregnancy chance with percentage
        chance_data = profile.get_pregnancy_chance_with_percentage()
        return chance_data

    def _get_owned_period(self, request, period_id):
        try:
            return Period.objects.get(
                id=period_id, customer=request.user.customer)
        except Period.DoesNotExist:
            raise HttpError(404, "Period not found")

    @staticmethod
    def _refresh_next_cycle_length(customer, after_start):
        """Recompute cycle_length of the period following `after_start`."""
        next_period = Period.objects.filter(
            customer=customer, start_date__gt=after_start
        ).order_by('start_date').first()
        if next_period:
            next_period.cycle_length = None
            next_period.save()

    @http_put(
        "{period_id}/",
        response={200: PeriodOutSchema},
    )
    def update_period(self, request, period_id: UUID, data: PeriodUpdateSchema):
        """Edit the start/end dates of any of the customer's periods."""
        if data.end_date < data.start_date:
            raise HttpError(400, "End date cannot be before start date")
        period_entry = self._get_owned_period(request, period_id)
        customer = period_entry.customer
        old_start = period_entry.start_date

        overlap = Period.objects.filter(
            customer=customer,
            start_date__date__lte=data.end_date,
            end_date__date__gte=data.start_date,
        ).exclude(id=period_entry.id).exists()
        if overlap:
            raise HttpError(400, "These dates overlap another period")

        period_entry.start_date = datetime.combine(
            data.start_date, datetime.min.time())
        period_entry.end_date = datetime.combine(
            data.end_date, datetime.min.time())
        period_entry.cycle_length = None  # recalculated in save()
        period_entry.save()

        self._refresh_next_cycle_length(customer, old_start)
        self._refresh_next_cycle_length(customer, period_entry.start_date)
        return period_entry

    @http_delete(
        "{period_id}/",
        response={200: SuccessSchema},
    )
    def delete_period(self, request, period_id: UUID):
        """Permanently delete one of the customer's periods."""
        period_entry = self._get_owned_period(request, period_id)
        customer = period_entry.customer
        start = period_entry.start_date
        period_entry.delete(hard=True)
        self._refresh_next_cycle_length(customer, start)
        return {"detail": {
            "title": "Deleted",
            "message": "Period deleted successfully",
        }}
