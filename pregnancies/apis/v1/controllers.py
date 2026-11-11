from datetime import date
from typing import List

from ninja.errors import HttpError
from ninja_extra import (
    api_controller, http_get, http_post, http_put, http_patch, http_delete)

from accounts.apis.v1.permissions import IsCustomer
from periods.models import Period
from general.apis.v1.schemas import SuccessSchema
from pregnancies.models import (
    Appointment, ChecklistItem, ChildWeightEntry, Pregnancy)
from pregnancies.services import build_dashboard
from pregnancies.apis.v1.schemas import (
    PregnancyInputSchema,
    PregnancyUpdateSchema,
    PregnancyOutputSchema,
    PregnancyEndSchema,
    PregnancyStatusSchema,
    SuccessMessageSchema,
    AppointmentInputSchema, AppointmentOutputSchema,
    ChecklistOutputSchema, ChecklistItemCreateSchema,
    ChecklistItemUpdateSchema,
    ChildWeightInputSchema, ChildWeightOutputSchema,
    PregnancyDashboardSchema,
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


    @http_get(
        'dashboard/',
        response={200: PregnancyDashboardSchema}
    )
    def get_dashboard(self, request):
        """
        Everything the pregnancy-mode Home and Analysis tabs need: week and
        trimester, baby development, maternal weight, last-7-day health
        metrics, symptom trends and the next appointment.
        """
        customer = request.user.customer
        pregnancy = Pregnancy.get_active_pregnancy(customer)
        if not pregnancy:
            raise HttpError(404, "No active pregnancy found")
        return build_dashboard(customer, pregnancy)


DEFAULT_CHECKLIST = {
    'mom': ['Maternity Clothes', 'Toiletries', 'Insurance Papers',
            'Birth Plan', 'Nursing Bra', 'ID & Hospital Documents'],
    'baby': ['Baby Clothes', 'Diapers', 'Blanket', 'Car Seat', 'Baby Wipes'],
    'other': ['Phone Charger', 'Snacks', 'Pillow'],
}
CHECKLIST_META = {
    'mom': ("Mom's Essentials", 'user', '#FF6B6B'),
    'baby': ("Baby's Essentials", 'smile', '#4ECDC4'),
    'other': ('Other Items', 'bag', '#45B7D1'),
}


def age_label(months):
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''}"
    years, rem = divmod(months, 12)
    label = f"{years} year{'s' if years > 1 else ''}"
    return f"{label} {rem}m" if rem else label


@api_controller('pregnancy/', tags=['Pregnancy'], permissions=[IsCustomer])
class PregnancyToolsAPIController:
    """Appointments, hospital-bag checklist and child weight tracking."""

    # ----------------------------------------------------------- Appointments
    @http_get('appointments/', response=List[AppointmentOutputSchema])
    def list_appointments(self, request, upcoming: bool = False):
        qs = Appointment.objects.filter(customer=request.user.customer)
        if upcoming:
            qs = qs.filter(date__gte=date.today(), is_completed=False)
        return list(qs.order_by('date', 'time'))

    @http_post('appointments/', response={201: AppointmentOutputSchema})
    def create_appointment(self, request, payload: AppointmentInputSchema):
        appointment = Appointment.objects.create(
            customer=request.user.customer, **payload.dict())
        return 201, appointment

    def _appointment(self, request, appointment_id):
        appointment = Appointment.objects.filter(
            id=appointment_id, customer=request.user.customer).first()
        if not appointment:
            raise HttpError(404, "Appointment not found")
        return appointment

    @http_put('appointments/{appointment_id}/',
              response=AppointmentOutputSchema)
    def update_appointment(self, request, appointment_id: int,
                           payload: AppointmentInputSchema):
        appointment = self._appointment(request, appointment_id)
        for field, value in payload.dict().items():
            setattr(appointment, field, value)
        appointment.save()
        return appointment

    @http_delete('appointments/{appointment_id}/',
                 response={200: SuccessSchema})
    def delete_appointment(self, request, appointment_id: int):
        self._appointment(request, appointment_id).delete()
        return {"detail": {
            "title": "Deleted", "message": "Appointment removed"}}

    # -------------------------------------------------------------- Checklist
    def _checklist(self, customer):
        items = list(ChecklistItem.objects.filter(customer=customer))
        if not items:
            ChecklistItem.objects.bulk_create([
                ChecklistItem(customer=customer, category=cat, label=label,
                              order=i)
                for cat, labels in DEFAULT_CHECKLIST.items()
                for i, label in enumerate(labels)
            ])
            items = list(ChecklistItem.objects.filter(customer=customer))

        categories = []
        for cat, (label, icon, color) in CHECKLIST_META.items():
            categories.append({
                'id': cat, 'label': label, 'icon': icon, 'color': color,
                'items': [i for i in items if i.category == cat],
            })
        return {
            'categories': categories,
            'packed_count': sum(1 for i in items if i.checked),
            'total_count': len(items),
        }

    @http_get('checklist/', response=ChecklistOutputSchema)
    def get_checklist(self, request):
        """Hospital bag checklist (default items are created on first use)."""
        return self._checklist(request.user.customer)

    @http_post('checklist/items/', response={201: ChecklistOutputSchema})
    def add_checklist_item(self, request, payload: ChecklistItemCreateSchema):
        customer = request.user.customer
        self._checklist(customer)  # make sure defaults exist first
        last = ChecklistItem.objects.filter(
            customer=customer, category=payload.category
        ).order_by('-order').first()
        ChecklistItem.objects.create(
            customer=customer, category=payload.category,
            label=payload.label.strip(), is_custom=True,
            order=(last.order + 1) if last else 0,
        )
        return 201, self._checklist(customer)

    @http_patch('checklist/items/{item_id}/', response=ChecklistOutputSchema)
    def update_checklist_item(self, request, item_id: int,
                              payload: ChecklistItemUpdateSchema):
        customer = request.user.customer
        item = ChecklistItem.objects.filter(
            id=item_id, customer=customer).first()
        if not item:
            raise HttpError(404, "Checklist item not found")
        if payload.checked is not None:
            item.checked = payload.checked
        if payload.label is not None:
            item.label = payload.label.strip()
        item.save()
        return self._checklist(customer)

    @http_delete('checklist/items/{item_id}/', response=ChecklistOutputSchema)
    def delete_checklist_item(self, request, item_id: int):
        customer = request.user.customer
        item = ChecklistItem.objects.filter(
            id=item_id, customer=customer).first()
        if not item:
            raise HttpError(404, "Checklist item not found")
        if not item.is_custom:
            raise HttpError(400, "Only items you added can be deleted")
        item.delete()
        return self._checklist(customer)

    # ----------------------------------------------------------- Child weight
    @http_get('child-weights/', response=List[ChildWeightOutputSchema])
    def list_child_weights(self, request):
        """Child weight history (oldest first) with gain since previous."""
        entries = ChildWeightEntry.objects.filter(
            customer=request.user.customer).order_by(
                'entry_date', 'created_at')
        result, previous = [], None
        for e in entries:
            kg = float(e.weight_kg)
            result.append({
                'id': e.id,
                'entry_date': e.entry_date,
                'age_months': e.age_months,
                'age_label': age_label(e.age_months),
                'weight_kg': kg,
                'gain_kg': round(kg - previous, 2) if previous is not None else 0,
            })
            previous = kg
        return result

    @http_post('child-weights/', response={201: ChildWeightOutputSchema})
    def add_child_weight(self, request, payload: ChildWeightInputSchema):
        customer = request.user.customer
        previous = ChildWeightEntry.objects.filter(
            customer=customer, entry_date__lte=payload.entry_date
        ).order_by('-entry_date', '-created_at').first()
        entry = ChildWeightEntry.objects.create(
            customer=customer,
            entry_date=payload.entry_date,
            age_months=payload.age_months,
            weight_kg=round(payload.weight_kg, 2),
        )
        kg = float(entry.weight_kg)
        return 201, {
            'id': entry.id,
            'entry_date': entry.entry_date,
            'age_months': entry.age_months,
            'age_label': age_label(entry.age_months),
            'weight_kg': kg,
            'gain_kg': round(kg - float(previous.weight_kg), 2) if previous else 0,
        }

    @http_delete('child-weights/{entry_id}/', response={200: SuccessSchema})
    def delete_child_weight(self, request, entry_id: int):
        deleted, _ = ChildWeightEntry.objects.filter(
            id=entry_id, customer=request.user.customer).delete()
        if not deleted:
            raise HttpError(404, "Weight entry not found")
        return {"detail": {"title": "Deleted", "message": "Entry removed"}}
