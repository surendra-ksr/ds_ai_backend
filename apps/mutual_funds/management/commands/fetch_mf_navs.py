import requests
import datetime
from django.core.management.base import BaseCommand, CommandError
from mutual_funds.models import MutualFundScheme, MutualFundNAV

# This URL is a common endpoint for fetching historical NAV data from AMFI.
AMFI_HISTORY_URL = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"

class Command(BaseCommand):
    help = 'Fetches historical NAV data for specified mutual fund schemes.'

    def add_arguments(self, parser):
        parser.add_argument('scheme_codes', nargs='+', type=int, help='A list of AMFI scheme codes to fetch NAV history for.')

    def handle(self, *args, **options):
        scheme_codes = options['scheme_codes']
        today = datetime.date.today()

        for scheme_code in scheme_codes:
            try:
                scheme = MutualFundScheme.objects.get(scheme_code=scheme_code)
                self.stdout.write(f"Processing scheme: {scheme.name} ({scheme_code})")
            except MutualFundScheme.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Scheme with code {scheme_code} not found in the database. Skipping."))
                continue

            # Determine the start date for fetching data
            latest_nav = MutualFundNAV.objects.filter(scheme=scheme).order_by('-date').first()
            start_date = latest_nav.date + datetime.timedelta(days=1) if latest_nav else datetime.date(2000, 1, 1)

            self.stdout.write(f"Fetching NAV data from {start_date.strftime('%d-%b-%Y')} to {today.strftime('%d-%b-%Y')}")

            # Loop through 90-day intervals
            current_start = start_date
            total_navs_saved = 0
            while current_start <= today:
                end_date = current_start + datetime.timedelta(days=89)
                if end_date > today:
                    end_date = today

                params = {
                    'SchemeCode': scheme_code,
                    'FromDate': current_start.strftime('%d-%b-%Y'),
                    'ToDate': end_date.strftime('%d-%b-%Y')
                }

                try:
                    response = requests.get(AMFI_HISTORY_URL, params=params)
                    response.raise_for_status()

                    if "No data found" in response.text or not response.text.strip():
                        # Move to the next interval if no data is found for the current one
                        current_start = end_date + datetime.timedelta(days=1)
                        continue

                    lines = response.text.strip().split('\r\n')
                    navs_to_create = []
                    for line in lines:
                        if ';' not in line:
                            continue
                        
                        parts = line.strip().split(';')
                        if len(parts) < 8 or not parts[0].isdigit():
                            continue

                        # Data format: Scheme Code;Scheme Name;ISIN;...;Net Asset Value;Date
                        nav_date_str = parts[7]
                        nav_value = parts[4]
                        nav_date = datetime.datetime.strptime(nav_date_str, '%d-%b-%Y').date()

                        navs_to_create.append(
                            MutualFundNAV(
                                scheme=scheme,
                                date=nav_date,
                                nav=float(nav_value)
                            )
                        )
                    
                    if navs_to_create:
                        MutualFundNAV.objects.bulk_create(navs_to_create, ignore_conflicts=True)
                        total_navs_saved += len(navs_to_create)

                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f"HTTP Error fetching data for {scheme_code} in range {current_start}-{end_date}: {e}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"An error occurred processing NAV data for {scheme_code}: {e}"))

                # Move to the next time interval
                current_start = end_date + datetime.timedelta(days=1)

            if total_navs_saved > 0:
                self.stdout.write(self.style.SUCCESS(f"Successfully saved {total_navs_saved} new NAV records for {scheme.name}."))
            else:
                self.stdout.write(self.style.SUCCESS(f"No new NAV records found for {scheme.name}. Data is up-to-date."))
