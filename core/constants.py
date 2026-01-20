from django.core.validators import RegexValidator

# Validators

PHONE_NUMBER_REGEX = r"^\+?[0-9]+$"
PhoneRegexValidator = RegexValidator(
    PHONE_NUMBER_REGEX,
    message="Please enter a valid phone number containing only numbers and an optional '+' at the start.",
    code="invalid_phone"
)
