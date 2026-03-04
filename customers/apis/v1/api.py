from .controllers import (
    CustomerOpenAPIController, CustomerAPIController,
    CustomerDiaryAPIController, CustomerReminderAPIController)

# This list makes it easy for the central API to find them
register_controllers = [
    CustomerOpenAPIController, CustomerAPIController,
    CustomerDiaryAPIController, CustomerReminderAPIController]
