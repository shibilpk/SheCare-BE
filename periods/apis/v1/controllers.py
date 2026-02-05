from accounts.apis.v1.permissions import IsCustomer
from ninja_extra import api_controller, http_get, http_post, paginate, route
from ninja.errors import HttpError
from ninja_extra.pagination import PageNumberPaginationExtra, PaginatedResponseSchema
from periods.models import Period
from .schemas import (
    PeriodDetailedOutSchema,
    PeriodOutSchema,
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
        "create/",
        response={200: PeriodOutSchema},
    )
    def create_period(self, request, data: PeriodOutSchema):
        """
        Create a new period entry for the authenticated customer
        """
        user = request.user
        customer = user.customer

        period_entry = Period.get_active_period(customer)
        if period_entry:
            period_entry.start_date = data.start_date
            period_entry.end_date = data.end_date
            period_entry.is_active = False
            period_entry.save()
        else:

            period_entry = Period.objects.create(
                customer=customer,
                start_date=data.start_date,
                end_date=data.end_date,
            )

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
