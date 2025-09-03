from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from decimal import Decimal
from apps.mutual_funds.models import MutualFundScheme

# This is a placeholder for a real web scraping implementation.
# In a real-world scenario, you would scrape the AMFI website for the latest AUM reports.
MOCK_AUM_DATA = {
    120584: Decimal("75000.50"), # HDFC Index Fund - S&P BSE Sensex Direct Plan (Example)
    118834: Decimal("450.20"),   # A smaller fund (Example)
    119598: Decimal("25000.00"), # ICICI Prudential Bluechip Fund Direct Plan Growth (Example)
}

class Command(BaseCommand):
    """Updates the Assets Under Management (AUM) for all mutual fund schemes."""
    help = 'Fetches and updates the AUM for all mutual fund schemes in the database.'

    def handle(self, *args, **options):
        self.stdout.write("Updating AUM for mutual fund schemes...")

        schemes_to_update = MutualFundScheme.objects.all()
        updated_count = 0

        # In a real implementation, you would fetch and parse a report from AMFI here.
        # For this example, we use our mock data dictionary.
        for scheme in tqdm(schemes_to_update, desc="Updating AUMs"):
            if scheme.scheme_code in MOCK_AUM_DATA:
                scheme.aum = MOCK_AUM_DATA[scheme.scheme_code]
                scheme.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"AUM update complete. Updated {updated_count} schemes."))
