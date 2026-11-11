from .controllers import (
    AuthAPIController, OTPAuthAPIController, AccountAPIController)

# This list makes it easy for the central API to find them
register_controllers = [
    AuthAPIController, OTPAuthAPIController, AccountAPIController]
