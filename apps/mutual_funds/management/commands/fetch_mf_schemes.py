import requests
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from tqdm import tqdm
from decimal import Decimal
from apps.mutual_funds.models import MutualFundHouse, MutualFundScheme
from apps.core.models import Category

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
AUM_THRESHOLD = Decimal("500.00") # 500 Crores

class Command(BaseCommand):
    help = 'Fetches all mutual fund schemes, updates their AUM, and filters out small funds.'

    def handle(self, *args, **options):
        # --- Step 1: Fetch all schemes from AMFI ---
        self.stdout.write("Step 1/3: Fetching mutual fund scheme data from AMFI...")
        
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

                # Robust Category Assignment: Use get_or_create to avoid KeyErrors.
                # This makes the command self-sufficient and removes the need for a separate seeding command.
                scheme.categories.clear()
                name_lower = scheme_name.lower()
                if 'equity' in name_lower: scheme.categories.add(Category.objects.get_or_create(name="Equity Fund")[0])
                if 'debt' in name_lower: scheme.categories.add(Category.objects.get_or_create(name="Debt Fund")[0])
                if 'hybrid' in name_lower: scheme.categories.add(Category.objects.get_or_create(name="Hybrid Fund")[0])
                if 'index' in name_lower: scheme.categories.add(Category.objects.get_or_create(name="Index Fund")[0])
                if 'tax' in name_lower or 'elss' in name_lower: scheme.categories.add(Category.objects.get_or_create(name="ELSS (Tax Saver)")[0])
                if 'large cap' in name_lower: scheme.categories.add(Category.objects.get_or_create(name="Large Cap")[0])
                if 'mid cap' in name_lower: scheme.categories.add(Category.objects.get_or_create(name="Mid Cap")[0])
                if 'small cap' in name_lower: scheme.categories.add(Category.objects.get_or_create(name="Small Cap")[0])

            self.stdout.write(self.style.SUCCESS(f"\nStep 1 complete. Created: {created_count}, Updated: {updated_count} schemes."))

        except Exception as e:
            raise CommandError(f'An error occurred during scheme fetching: {e}')

        # --- Step 2: Update AUM for all schemes ---
        self.stdout.write("\nStep 2/3: Calling command to update AUM for all schemes...")
        try:
            call_command('update_mf_aum')
            self.stdout.write(self.style.SUCCESS("Step 2 complete. AUM data has been updated."))
        except Exception as e:
            raise CommandError(f'An error occurred during AUM update: {e}')

        # --- Step 3: Filter out small funds ---
        self.stdout.write(f"\nStep 3/3: Removing funds with AUM less than {AUM_THRESHOLD} Crores or with no AUM data...")
        
        schemes_to_delete = MutualFundScheme.objects.filter(aum__lt=AUM_THRESHOLD) | MutualFundScheme.objects.filter(aum__isnull=True)
        
        delete_count = schemes_to_delete.count()

        if delete_count > 0:
            schemes_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"Step 3 complete. Removed {delete_count} small or un-tracked funds."))
        else:
            self.stdout.write(self.style.SUCCESS("Step 3 complete. No funds needed to be removed."))

        self.stdout.write(self.style.SUCCESS("\nMutual fund scheme processing is fully complete."))
