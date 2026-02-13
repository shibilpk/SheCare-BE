from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from general.constants import LanguageChoice
from general.models import DailyTip
from core.utils.ai import AIService


class Command(BaseCommand):
    help = 'Populate daily tips using AI for a specific date or date range'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to generate tip for (format: YYYY-MM-DD)',
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for range (format: YYYY-MM-DD)',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for range (format: YYYY-MM-DD)',
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Number of days from today to generate tips for',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing tips',
        )
        parser.add_argument(
            '--lang',
            type=str,
            default='en',
            choices=[choice[0] for choice in LanguageChoice.choices],
            help='Language for AI (default: en)',
        )

    def handle(self, *args, **options):
        ai_service = AIService()
        dates_to_process = []

        # Determine which dates to process
        if options['date']:
            # Single date
            try:
                target_date = datetime.strptime(
                    options['date'], '%Y-%m-%d').date()
                dates_to_process.append(target_date)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return

        elif options['start_date'] and options['end_date']:
            # Date range
            try:
                start = datetime.strptime(
                    options['start_date'], '%Y-%m-%d').date()
                end = datetime.strptime(options['end_date'], '%Y-%m-%d').date()

                if start > end:
                    self.stdout.write(
                        self.style.ERROR('Start date must be before end date')
                    )
                    return

                current = start
                while current <= end:
                    dates_to_process.append(current)
                    current += timedelta(days=1)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return

        elif options['days']:
            # Generate for next N days
            today = timezone.now().date()
            for i in range(options['days']):
                dates_to_process.append(today + timedelta(days=i))

        else:
            # Default: generate for today
            dates_to_process.append(timezone.now().date())

        lang = options['lang']
        lang_full = dict(LanguageChoice.choices)

        # Process each date
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for target_date in dates_to_process:
            # Check if tip already exists
            existing_tip = DailyTip.objects.filter(date=target_date).first()

            if existing_tip and not options['overwrite']:
                self.stdout.write(
                    self.style.WARNING(
                        f'Tip for {target_date} already exists. Skipping...')
                )
                skipped_count += 1
                continue

            # Generate tip using AI
            self.stdout.write(f'Generating tip for {target_date}...')

            prompt = f"""Generate a daily health tip for women's wellness for {target_date.strftime('%B %d, %Y')} in {lang_full[lang]}.

                    The tip should be:
                    1. SHORT_DESCRIPTION: A brief, actionable tip in 1-2 sentences (max 150 characters)
                    2. LONG_DESCRIPTION: A detailed explanation with practical advice (3-4 paragraphs)

                    Topics can include: menstrual health, nutrition, exercise, mental wellness, pregnancy care, hormonal balance, self-care, etc.

                    Format your response EXACTLY as:
                    SHORT_DESCRIPTION: [your short tip here]
                    LONG_DESCRIPTION: [your detailed explanation here]"""

            try:
                response = ai_service.generate_report_logic(prompt)

                # Parse the response
                if "SHORT_DESCRIPTION:" in response and "LONG_DESCRIPTION:" in response:
                    parts = response.split("LONG_DESCRIPTION:")
                    short_desc = parts[0].replace(
                        "SHORT_DESCRIPTION:", "").strip()
                    long_desc = parts[1].strip()

                    # Create or update the tip
                    if existing_tip:
                        existing_tip.short_description = short_desc
                        existing_tip.long_description = long_desc
                        existing_tip.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Updated tip for {target_date}')
                        )
                    else:
                        DailyTip.objects.create(
                            date=target_date,
                            short_description=short_desc,
                            long_description=long_desc,
                            language=lang
                        )
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Created tip for {target_date}')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to parse AI response for {target_date}')
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error generating tip for {target_date}: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count}'))
        self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
        self.stdout.write('='*50)
