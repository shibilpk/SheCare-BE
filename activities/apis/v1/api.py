from .controllers import (
    ActivitiesAPIController, HydrationAPIController, MedicationAPIController,
    NutritionAPIController, ExerciseAPIController, SleepAPIController)

register_controllers = [
    ActivitiesAPIController, HydrationAPIController, MedicationAPIController,
    NutritionAPIController, ExerciseAPIController, SleepAPIController]
