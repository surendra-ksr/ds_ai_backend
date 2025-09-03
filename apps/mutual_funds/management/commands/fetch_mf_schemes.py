import requests
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from apps.mutual_funds.models import MutualFundHouse, MutualFundScheme
from apps.core.models import Category
from apps.mutual_funds.data.major_mf_schemes import MAJOR_MF_SCHEMES

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

class Command(BaseCommand):
    help = 'Fetches all mutual fund schemes or only major ones and assigns categories.'

    def add_arguments(self, parser):
        parser.add_argument('--major-only', action='store_true', help='Fetch only major, curated mutual fund schemes.')

    def handle(self, *args, **options):
        self.stdout.write("Fetching mutual fund scheme data from AMFI...")
        category_map = {cat.name: cat for cat in Category.objects.all()}
        
        # Determine which schemes to process
        major_only = options['major_only']
        if major_only:
            self.stdout.write(self.style.SUCCESS("Processing only major, curated mutual fund schemes."))

        try:
            response = requests.get(AMFI_URL)
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            
            created_count = 0
            updated_count = 0

            for line in tqdm(lines, desc="Processing Schemes"):
                if ';' not in line or not line.strip(): continue
                parts = line.strip().split(';')
                if len(parts) < 6 or not parts[0].isdigit(): continue

                scheme_code = int(parts[0])

                # --- Filtering Logic ---
                if major_only and scheme_code not in MAJOR_MF_SCHEMES:
                    continue # Skip this scheme if it's not in our major list

                scheme_name = parts[3]
                isin = parts[1] if parts[1] != '-' else parts[2]

                if not isin or isin == '-': continue

                fund_house_name = " ".join(scheme_name.split()[:2]) + " Mutual Fund"
                fund_house, _ = MutualFundHouse.objects.get_or_create(name=fund_house_name)

                scheme, created = MutualFundScheme.objects.update_or_create(
                    isin=isin,
                    defaults={'scheme_code': scheme_code, 'fund_house': fund_house, 'name': scheme_name}
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                scheme.categories.clear()
                name_lower = scheme_name.lower()
                if 'equity' in name_lower: scheme.categories.add(category_map["Equity Fund"])
                if 'debt' in name_lower: scheme.categories.add(category_map["Debt Fund"])
                if 'hybrid' in name_lower: scheme.categories.add(category_map["Hybrid Fund"])
                if 'index' in name_lower: scheme.categories.add(category_map["Index Fund"])
                if 'tax' in name_lower or 'elss' in name_lower: scheme.categories.add(category_map["ELSS (Tax Saver)"])
                if 'large cap' in name_lower: scheme.categories.add(category_map["Large Cap"])
                if 'mid cap' in name_lower: scheme.categories.add(category_map["Mid Cap"])
                if 'small cap' in name_lower: scheme.categories.add(category_map["Small Cap"])

            self.stdout.write(self.style.SUCCESS(f"\nProcessing complete. Created: {created_count}, Updated: {updated_count}."))

        except Exception as e:
            raise CommandError(f'An error occurred: {e}')
