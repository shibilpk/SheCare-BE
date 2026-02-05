from .controllers import (
    CustomerOpenAPIController, CustomerAPIController,
    CustomerDiaryAPIController)

# This list makes it easy for the central API to find them
register_controllers = [
    CustomerOpenAPIController, CustomerAPIController,
    CustomerDiaryAPIController]
