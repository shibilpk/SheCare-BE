from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from accounts.apis.v1.controllers import AuthAPIController
from core.exceptions import ApiError
from customers.apis.v1.controllers import (
    CustomerAPIController, CustomerOpenAPIController)
from general.apis.v1.controllers import GeneralAPIController

# Create centralized API instance
api = NinjaExtraAPI(
    title="SheCare API",
    version="1.0.0",
    auth=JWTAuth(),
)


@api.exception_handler(ApiError)
def api_error_handler(request, exc: ApiError):
    # return Response(
    #     status=exc.status_code,
    #     data={
    #         "detail": {
    #             "title": exc.title,
    #             "message": exc.message,
    #         }
    #     }
    # )
    return api.create_response(
        request,
        {
            "detail": {
                "title": exc.title,
                "message": exc.message,
            }},
        status=exc.status_code,
    )

# @api.exception_handler(ValidationError)
# def custom_validation_error_handler(request, exc):
#     """
#     Custom handler for validation errors with state: 0
#     and field-based errors
#     """

#     errors = {}
#     error_list = exc.errors if isinstance(exc.errors, list) else exc.errors()

#     for error in error_list:
#         field = error.get("loc", ["unknown"])[-1]

#         if field not in errors:
#             errors[field] = []

#         msg = error.get("msg", "")

#         errors[field].append(msg)

#     return api.create_response(
#         request,
#         {"state": 0, **errors},
#         status=400,
#     )


# @api.exception_handler(AuthenticationError)
# def custom_auth_error_handler(request, exc):
#     """Custom handler for authentication errors"""
#     return api.create_response(
#         request,
#         {"detail": "Unauthorized"},
#         status=401,
#     )


# @api.exception_handler(HttpError)
# def custom_http_error_handler(request, exc):
#     """Custom handler for HTTP errors"""
#     return api.create_response(
#         request,
#         {"detail": exc.message if hasattr(exc, 'message') else str(exc)},
#         status=exc.status_code,
#     )


# Register all controllers
api.register_controllers(
    AuthAPIController,
    CustomerOpenAPIController,
    CustomerAPIController,
    GeneralAPIController,
)
