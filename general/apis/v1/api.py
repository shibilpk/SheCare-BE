from .controllers import (
    GeneralAPIController, BlogAPIController, StaticContentAPIController, ContactFeedbackAPIController)

# This list makes it easy for the central API to find them
register_controllers = [
    GeneralAPIController,
    BlogAPIController,
    StaticContentAPIController,
    ContactFeedbackAPIController
]
