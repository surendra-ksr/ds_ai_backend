import requests
from django.core.management.base import BaseCommand, CommandError
from mutual_funds.models import MutualFundHouse, MutualFundScheme
from core.models import Category

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

class Command(BaseCommand):
    help = 'Fetches all mutual fund schemes and assigns them to relevant categories.'

    def handle(self, *args, **options):
        self.stdout.write("Fetching mutual fund scheme data from AMFI...")

        # Pre-fetch category objects for efficiency
        category_map = {cat.name: cat for cat in Category.objects.all()}

        try:
            response = requests.get(AMFI_URL)
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            
            updated_count = 0
            created_count = 0

            for line in lines:
                if ';' not in line or not line.strip():
                    continue
                
                parts = line.strip().split(';')
                if len(parts) < 6 or not parts[0].isdigit():
                    continue

                scheme_code = int(parts[0])
                isin = parts[1] if parts[1] != '-' else parts[2]
                scheme_name = parts[3]
                fund_house_name = " ".join(scheme_name.split()[:2]) + " Mutual Fund"

                # Get or create the fund house
                fund_house, _ = MutualFundHouse.objects.get_or_create(name=fund_house_name)

                # Create or update the scheme object
                scheme, created = MutualFundScheme.objects.update_or_create(
                    scheme_code=scheme_code,
                    defaults={
                        'fund_house': fund_house,
                        'name': scheme_name,
                        'isin': isin
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # --- Smart Categorization Logic ---
                scheme.categories.clear() # Clear old categories before assigning new ones
                name_lower = scheme_name.lower()

                if 'equity' in name_lower:
                    scheme.categories.add(category_map["Equity Fund"])
                if 'debt' in name_lower or 'bond' in name_lower or 'gilt' in name_lower:
                    scheme.categories.add(category_map["Debt Fund"])
                if 'hybrid' in name_lower or 'balanced' in name_lower:
                    scheme.categories.add(category_map["Hybrid Fund"])
                if 'index' in name_lower or 'nifty' in name_lower or 'sensex' in name_lower:
                    scheme.categories.add(category_map["Index Fund"])
                if 'tax' in name_lower or 'elss' in name_lower:
                    scheme.categories.add(category_map["ELSS (Tax Saver)"])
                if 'large cap' in name_lower:
                    scheme.categories.add(category_map["Large Cap"])
                if 'mid cap' in name_lower:
                    scheme.categories.add(category_map["Mid Cap"])
                if 'small cap' in name_lower:
                    scheme.categories.add(category_map["Small Cap"])
                if 'liquid' in name_lower:
                    scheme.categories.add(category_map["Liquid Fund"])

            self.stdout.write(self.style.SUCCESS(
                f"Processing complete. Created: {created_count}, Updated: {updated_count}."
            ))

        except requests.exceptions.RequestException as e:
            raise CommandError(f'Failed to fetch data from AMFI. Error: {e}')
        except KeyError as e:
            raise CommandError(f"A required category ({e}) was not found. Run `seed_categories` first.")
        except Exception as e:
            raise CommandError(f'An error occurred: {e}')
