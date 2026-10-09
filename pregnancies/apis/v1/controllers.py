from ninja.errors import HttpError
from ninja_extra import api_controller, http_get, http_post, http_patch, http_delete

from accounts.apis.v1.permissions import IsCustomer
from periods.models import Period
from pregnancies.models import Pregnancy
from pregnancies.apis.v1.schemas import (
    PregnancyInputSchema,
    PregnancyUpdateSchema,
    PregnancyOutputSchema,
    PregnancyEndSchema,
    PregnancyStatusSchema,
    SuccessMessageSchema
)


@api_controller('pregnancy/', tags=['Pregnancy'], permissions=[IsCustomer])
class PregnancyAPIController:
    """API Controller for pregnancy management"""

    @http_get(
        'status/',
        response={200: PregnancyStatusSchema}
    )
    def get_pregnancy_status(self, request):
        """
        Check if customer has an active pregnancy
        Returns pregnancy data if exists
        """
        customer = request.user.customer
        pregnancy = Pregnancy.get_active_pregnancy(customer)

        return {
            "has_active_pregnancy": bool(pregnancy),
            "pregnancy": pregnancy
        }

    @http_get(
        'active/',
        response={200: PregnancyOutputSchema, 404: dict}
    )
    def get_active_pregnancy(self, request):
        """Get active pregnancy details"""
        customer = request.user.customer
        pregnancy = Pregnancy.get_active_pregnancy(customer)

        if not pregnancy:
            raise HttpError(404, "No active pregnancy found")

        return pregnancy

    @http_post(
        'create/',
        response={200: PregnancyOutputSchema}
    )
    def create_pregnancy(self, request, payload: PregnancyInputSchema):
        """Create a new pregnancy record"""
        customer = request.user.customer
        last_period = Period.get_last_period(customer)
        # Create pregnancy (last_period will be auto-set from most recent Period)
        pregnancy = Pregnancy.objects.create(
            customer=customer,
            due_date=payload.due_date,
            baby_name=payload.baby_name or "",
            doctor_name=payload.doctor_name or "",
            hospital_name=payload.hospital_name or "",
            last_period=last_period,
            is_active=True
        )
        return pregnancy

    @http_patch(
        'update/',
        response={200: PregnancyOutputSchema, 404: dict}
    )
    def update_pregnancy(self, request, payload: PregnancyUpdateSchema):
        """Update active pregnancy details"""
        customer = request.user.customer
        pregnancy = Pregnancy.get_active_pregnancy(customer)

        if not pregnancy:
            raise HttpError(404, "No active pregnancy found")

        # Update fields if provided (last_period is auto-set, can't be manually updated)
        if payload.due_date is not None:
            pregnancy.due_date = payload.due_date
        if payload.baby_name is not None:
            pregnancy.baby_name = payload.baby_name
        if payload.doctor_name is not None:
            pregnancy.doctor_name = payload.doctor_name
        if payload.hospital_name is not None:
            pregnancy.hospital_name = payload.hospital_name

        pregnancy.save()

        return pregnancy

    @http_post(
        'end/',
        response={200: SuccessMessageSchema, 404: dict}
    )
    def end_pregnancy(self, request, payload: PregnancyEndSchema):
        """
        End pregnancy with reason (born, lost, mistake)
        """
        customer = request.user.customer
        pregnancy = Pregnancy.get_active_pregnancy(customer)

        if not pregnancy:
            raise HttpError(404, "No active pregnancy found")

        if payload.reason == 'born':
            pregnancy.baby_born = True
            if payload.baby_details:
                pregnancy.child_name = payload.baby_details.child_name
                pregnancy.birth_date = payload.baby_details.birth_date
                pregnancy.birth_weight = payload.baby_details.birth_weight
                pregnancy.birth_length = payload.baby_details.birth_length
                pregnancy.child_gender = payload.baby_details.child_gender or ""

            pregnancy.save()
            return {
                "title": "Congratulations! 🎉",
                "message": f"Welcome to the world, {pregnancy.child_name or 'your baby'}!"
            }

        elif payload.reason == 'lost':
            pregnancy.pregnancy_lost = True
            pregnancy.save()
            return {
                "title": "Pregnancy Ended",
                "message": "Our thoughts are with you during this difficult time."
            }

        elif payload.reason == 'mistake':
            pregnancy.mistaken_toggle = True
            pregnancy.save()
            return {
                "title": "Pregnancy Mode Disabled",
                "message": "Pregnancy mode has been turned off."
            }

        raise HttpError(400, "Invalid reason provided")

    @http_delete(
        'delete/',
        response={200: SuccessMessageSchema, 404: dict}
    )
    def delete_pregnancy(self, request):
        """Delete active pregnancy"""
        customer = request.user.customer
        pregnancy = Pregnancy.get_active_pregnancy(customer)

        if not pregnancy:
            raise HttpError(404, "No active pregnancy found")

        pregnancy.delete()

        return {
            "title": "Success",
            "message": "Pregnancy record deleted successfully"
        }
