from django.core.management.base import BaseCommand
from activities.models import FoodSuggestion


class Command(BaseCommand):
    help = 'Populate food suggestions for nutrition autocomplete'

    def handle(self, *args, **kwargs):
        # Sample food data
        foods = [
            # Breakfast
            {"name": "Oatmeal with Berries", "calories": 320, "carbs": 52, "protein": 10, "fat": 8},
            {"name": "Greek Yogurt with Honey", "calories": 180, "carbs": 22, "protein": 15, "fat": 4},
            {"name": "Scrambled Eggs (2)", "calories": 140, "carbs": 2, "protein": 12, "fat": 10},
            {"name": "Whole Wheat Toast", "calories": 80, "carbs": 15, "protein": 4, "fat": 1},
            {"name": "Banana", "calories": 105, "carbs": 27, "protein": 1.3, "fat": 0.4},
            {"name": "Apple", "calories": 95, "carbs": 25, "protein": 0.5, "fat": 0.3},

            # Lunch
            {"name": "Grilled Chicken Salad", "calories": 420, "carbs": 28, "protein": 36, "fat": 16},
            {"name": "Chicken Breast (grilled)", "calories": 165, "carbs": 0, "protein": 31, "fat": 3.6},
            {"name": "Brown Rice (1 cup)", "calories": 215, "carbs": 45, "protein": 5, "fat": 1.8},
            {"name": "Quinoa (1 cup)", "calories": 220, "carbs": 39, "protein": 8, "fat": 3.6},
            {"name": "Mixed Green Salad", "calories": 35, "carbs": 7, "protein": 2, "fat": 0.5},
            {"name": "Avocado (half)", "calories": 120, "carbs": 6, "protein": 1.5, "fat": 11},

            # Dinner
            {"name": "Salmon (grilled)", "calories": 280, "carbs": 0, "protein": 39, "fat": 13},
            {"name": "Sweet Potato", "calories": 180, "carbs": 42, "protein": 4, "fat": 0.3},
            {"name": "Steamed Broccoli", "calories": 55, "carbs": 11, "protein": 3.7, "fat": 0.6},
            {"name": "Pasta (whole wheat)", "calories": 174, "carbs": 37, "protein": 7.5, "fat": 0.8},

            # Snacks
            {"name": "Almonds (handful)", "calories": 160, "carbs": 6, "protein": 6, "fat": 14},
            {"name": "Protein Bar", "calories": 200, "carbs": 24, "protein": 20, "fat": 6},
            {"name": "Hummus with Carrots", "calories": 150, "carbs": 18, "protein": 6, "fat": 7},
            {"name": "String Cheese", "calories": 80, "carbs": 1, "protein": 6, "fat": 6},

            # Drinks
            {"name": "Green Smoothie", "calories": 180, "carbs": 32, "protein": 6, "fat": 4},
            {"name": "Protein Shake", "calories": 220, "carbs": 18, "protein": 25, "fat": 5},

            # Indian
            {"name": "Dal (Lentils)", "calories": 230, "carbs": 40, "protein": 18, "fat": 0.8},
            {"name": "Chapati", "calories": 120, "carbs": 23, "protein": 3.5, "fat": 2},
            {"name": "Vegetable Curry", "calories": 180, "carbs": 25, "protein": 5, "fat": 8},
            {"name": "Chicken Curry", "calories": 320, "carbs": 15, "protein": 28, "fat": 18},
            {"name": "Idli (2 pieces)", "calories": 78, "carbs": 16, "protein": 2, "fat": 0.4},
            {"name": "Dosa", "calories": 168, "carbs": 28, "protein": 4, "fat": 4},
            {"name": "Paneer Tikka", "calories": 260, "carbs": 8, "protein": 18, "fat": 18},
        ]

        created_count = 0
        updated_count = 0

        for food_data in foods:
            food, created = FoodSuggestion.objects.update_or_create(
                name=food_data['name'],
                defaults={
                    'calories': food_data['calories'],
                    'carbs': food_data['carbs'],
                    'protein': food_data['protein'],
                    'fat': food_data['fat'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated food suggestions: '
                f'{created_count} created, {updated_count} updated'
            )
        )
