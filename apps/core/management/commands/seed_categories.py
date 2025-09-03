from django.core.management.base import BaseCommand
from apps.core.models import Category

# A comprehensive list of categories based on user requirements
CATEGORIES = [
    # Major Indices
    "Nifty 50", "Nifty Next 50", "Nifty 100", "Nifty 500", "Bank Nifty", "Nifty Financial Services",

    # Market Cap
    "Large Cap", "Mid Cap", "Small Cap",

    # Stock Sectors
    "IT", "Financial Services", "Energy", "Infrastructure", "Green Energy", "Healthcare", "FMCG", "Automobile",

    # Thematic / Factor-based (for Stocks & MFs)
    "High Dividend", "Value", "Growth", "Best PE Ratio",

    # Mutual Fund Specific
    "Equity Fund", "Debt Fund", "Hybrid Fund", "Index Fund", "ELSS (Tax Saver)", "Liquid Fund",
]

class Command(BaseCommand):
    help = 'Seeds the database with an initial list of categories for stocks and mutual funds.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories...")
        created_count = 0
        for category_name in CATEGORIES:
            _, created = Category.objects.get_or_create(name=category_name)
            if created:
                created_count += 1
                self.stdout.write(f"  - Created category: {category_name}")
        
        self.stdout.write(self.style.SUCCESS(f"Seeding complete. {created_count} new categories were added."))
