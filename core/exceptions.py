from rest_framework.views import exception_handler
from core.helpers import generate_serializer_errors

def handler(exc, context):
    """
    TODO write the docs
    TODO handle nested field errors
    """
    response = exception_handler(exc, context)

    if response is None:
        return response

    message = generate_serializer_errors(response.data)

    response.data['message'] = message
    return response
