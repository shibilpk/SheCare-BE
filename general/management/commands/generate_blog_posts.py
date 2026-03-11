import json
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from general.models import BlogPost
from core.utils.ai import AIService


class Command(BaseCommand):
    help = 'Generate blog posts using AI about women\'s health topics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of blog posts to generate (default: 5)'
        )
        parser.add_argument(
            '--topics',
            type=str,
            help='Comma-separated list of specific topics to write about'
        )
        parser.add_argument(
            '--author',
            type=str,
            default='Dr. Sarah Wilson',
            help='Author name for blog posts'
        )

    def handle(self, *args, **options):
        count = options['count']
        author = options['author']
        custom_topics = options.get('topics')

        # Default women's health topics
        default_topics = [
            "Understanding Your Menstrual Cycle",
            "Nutrition Tips for Women's Health",
            "Managing PMS Symptoms Naturally",
            "The Importance of Regular Exercise",
            "Mental Health and Hormonal Changes",
            "Pregnancy Planning and Preparation",
            "Postpartum Recovery Tips",
            "Managing Menopause Symptoms",
            "Breast Health Awareness",
            "Calcium and Bone Health",
            "Sleep and Women's Health",
            "Stress Management Techniques",
            "Understanding PCOS",
            "Endometriosis: What You Need to Know",
            "Heart Health for Women",
            "Healthy Skin Care Routines",
            "Fiber and Digestive Health",
            "Vitamins and Supplements for Women",
            "Yoga for Women's Wellness",
            "Understanding Fertility and Ovulation",
            "Mental Health and Self-Care",
            "The Role of Hydration in Women's Health",
            "Sexual Health and Wellness",
            "The Benefits of Meditation",
            "Understanding Thyroid Health",
            "Managing Anxiety and Depression",
            "The Importance of Regular Health Checkups",
            "Understanding Hormonal Imbalances",
            "Healthy Aging Tips for Women"

        ]

        # Use custom topics if provided
        if custom_topics:
            topics = [t.strip() for t in custom_topics.split(',')]
        else:
            topics = default_topics[:count]

        ai_service = AIService()
        created_count = 0
        failed_count = 0

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting to generate {count} blog posts...\n'
            )
        )

        for i, topic in enumerate(topics[:count], 1):
            try:
                self.stdout.write(f'{i}/{count} Generating: "{topic}"...')

                if BlogPost.objects.filter(title=topic).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Blog post with title "{topic}" already exists. Skipping.'
                        )
                    )
                    continue

                # Generate blog content using AI
                blog_data = self.generate_blog_with_ai(
                    ai_service,
                    topic,
                    author
                )

                if not blog_data:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to generate content')
                    )
                    failed_count += 1
                    continue

                # Create blog post
                blog_post = BlogPost.objects.create(
                    title=topic,
                    content=json.dumps(blog_data['content']),
                    author=author,
                    published_date=date.today() - timedelta(days=count - i)
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Created: {blog_post.title[:50]}...'
                    )
                )
                created_count += 1

                import time
                time.sleep(60)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error: {str(e)}')
                )
                failed_count += 1
                continue

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successfully created: {created_count}')
        )
        if failed_count > 0:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed: {failed_count}')
            )
        self.stdout.write('=' * 50 + '\n')

    def generate_blog_with_ai(self, ai_service, topic, author):
        """
        Generate blog content using AI and convert it to EditorJS format
        """
        prompt = f"""
Write a comprehensive, informative blog post about "{topic}"
for a women's health app. The post should be:

- Educational and evidence-based
- Written in a friendly, accessible tone
- Around 400-600 words
- Include practical tips or advice
- Structured with clear sections

Please provide the content in the following format:
TITLE: [A catchy, clear title]
INTRO: [A brief 1-2 sentence introduction]
SECTIONS: [Main content divided into clear sections with headings]
CONCLUSION: [A brief conclusion with actionable takeaway]

Focus on accuracy, empowerment, and practical information.
"""

        try:
            # Get AI response
            response = ai_service.generate_report_logic(prompt)

            if not response or response.startswith("Error"):
                return None

            # Parse the AI response
            blog_data = self.parse_ai_response(response, topic)
            return blog_data

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'AI Generation Error: {str(e)}')
            )
            return None

    def parse_ai_response(self, response, fallback_title):
        """
        Parse AI response and convert to EditorJS format
        """
        lines = response.strip().split('\n')
        title = fallback_title
        blocks = []

        # Try to extract title
        for line in lines:
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
                break

        # Convert content to EditorJS blocks
        current_paragraph = []

        for line in lines:
            line = line.strip()

            # Skip empty lines and metadata lines
            if (
                not line or
                line.startswith('TITLE:') or
                line.startswith('INTRO:') or
                line.startswith('SECTIONS:') or
                line.startswith('CONCLUSION:')
            ):
                if current_paragraph:
                    blocks.append({
                        "type": "paragraph",
                        "data": {
                            "text": " ".join(current_paragraph)
                        }
                    })
                    current_paragraph = []
                continue

            # Detect headers (lines ending with : or starting with ##)
            if (
                line.endswith(':') and len(line) < 60 and
                not line.startswith('-')
            ) or line.startswith('##'):
                if current_paragraph:
                    blocks.append({
                        "type": "paragraph",
                        "data": {
                            "text": " ".join(current_paragraph)
                        }
                    })
                    current_paragraph = []

                header_text = line.replace('##', '').replace(':', '').strip()
                blocks.append({
                    "type": "header",
                    "data": {
                        "text": header_text,
                        "level": 2
                    }
                })

            # Detect list items
            elif line.startswith('-') or line.startswith('•'):
                if current_paragraph:
                    blocks.append({
                        "type": "paragraph",
                        "data": {
                            "text": " ".join(current_paragraph)
                        }
                    })
                    current_paragraph = []

                # Check if last block is a list, if not create new one
                if blocks and blocks[-1]["type"] == "list":
                    blocks[-1]["data"]["items"].append(
                        line.lstrip('-•').strip()
                    )
                else:
                    blocks.append({
                        "type": "list",
                        "data": {
                            "style": "unordered",
                            "items": [line.lstrip('-•').strip()]
                        }
                    })

            # Regular paragraph text
            else:
                current_paragraph.append(line)

        # Add remaining paragraph
        if current_paragraph:
            blocks.append({
                "type": "paragraph",
                "data": {
                    "text": " ".join(current_paragraph)
                }
            })

        # Ensure we have at least one block
        if not blocks:
            blocks.append({
                "type": "paragraph",
                "data": {
                    "text": response[:500]  # Use first 500 chars as fallback
                }
            })

        return {
            "title": title,
            "content": {
                "time": int(timezone.now().timestamp() * 1000),
                "blocks": blocks,
                "version": "2.28.0"
            }
        }
