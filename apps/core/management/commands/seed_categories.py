from django.core.management.base import BaseCommand
from apps.core.models import Category

# Define the essential categories required by the application
REQUIRED_CATEGORIES = [
    "Equity Fund",
    "Debt Fund",
    "Hybrid Fund",
    "Index Fund",
    "ELSS (Tax Saver)",
    "Large Cap",
    "Mid Cap",
    "Small Cap",
]

class Command(BaseCommand):
    """Seeds the database with essential asset categories."""
    help = 'Creates predefined categories required for the application to function correctly.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding essential categories...")
        created_count = 0
        for category_name in REQUIRED_CATEGORIES:
            _, created = Category.objects.get_or_create(name=category_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  -> Created category: "{category_name}"'))
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Category seeding complete. {created_count} new categories were added."))
