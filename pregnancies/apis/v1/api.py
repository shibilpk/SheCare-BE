from .controllers import PregnancyAPIController, PregnancyToolsAPIController

# This list makes it easy for the central API to find them
register_controllers = [PregnancyAPIController, PregnancyToolsAPIController]
