from ninja_extra.permissions import BasePermission


class IsCustomer(BasePermission):
    """
    Allows access only to users with a customer profile
    """

    def has_permission(self, request, controller):
        user = request.user
        return bool(
            user and user.is_authenticated and hasattr(user, "customer"))
