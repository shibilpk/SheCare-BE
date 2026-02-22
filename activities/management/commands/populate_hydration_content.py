from django.core.management.base import BaseCommand
from activities.models import HydrationContent


class Command(BaseCommand):
    help = 'Populate hydration benefits and tips'

    def handle(self, *args, **options):
        # Clear existing content
        HydrationContent.objects.all().delete()

        # Add benefits
        benefits = [
            {'icon': '💪', 'text': 'Supports healthy amniotic fluid levels', 'order': 1},
            {'icon': '🌡️', 'text': 'Regulates body temperature', 'order': 2},
            {'icon': '✨', 'text': 'Reduces swelling and prevents constipation', 'order': 3},
            {'icon': '⚡', 'text': 'Boosts energy levels', 'order': 4},
        ]

        for benefit in benefits:
            HydrationContent.objects.create(
                content_type='benefit',
                icon=benefit['icon'],
                text=benefit['text'],
                order=benefit['order'],
                is_active=True
            )

        # Add tips
        tips = [
            {'icon': '💧', 'text': 'Keep a water bottle with you at all times', 'order': 1},
            {'icon': '🍽️', 'text': 'Drink a glass of water before each meal', 'order': 2},
            {'icon': '🍋', 'text': 'Add lemon or cucumber for flavor', 'order': 3},
            {'icon': '⏰', 'text': 'Set hourly reminders on your phone', 'order': 4},
        ]

        for tip in tips:
            HydrationContent.objects.create(
                content_type='tip',
                icon=tip['icon'],
                text=tip['text'],
                order=tip['order'],
                is_active=True
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(benefits)} benefits and {len(tips)} tips')
        )
