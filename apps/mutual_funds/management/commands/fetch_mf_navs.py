import requests
import datetime
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from apps.mutual_funds.models import MutualFundScheme, MutualFundNAV

AMFI_HISTORY_URL = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"

# Concurrently fetch data, but not so many as to get blocked.
MAX_WORKERS = 5


class Command(BaseCommand):
    """
    Fetches historical NAV data for mutual funds from the AMFI portal.
    It uses a thread pool for concurrent fetching to improve performance and includes robust error handling.
    """
    help = 'Fetches historical NAV data for one or all mutual fund schemes concurrently.'

    def add_arguments(self, parser):
        parser.add_argument('scheme_codes', nargs='*', type=int, help='Optional list of AMFI scheme codes to fetch.')
        parser.add_argument('--all', action='store_true', help='Fetch NAV history for all schemes in the database.')

    def handle(self, *args, **options):
        schemes_to_process = []
        if options['all']:
            schemes_to_process = MutualFundScheme.objects.all()
            if not schemes_to_process.exists():
                raise CommandError("No mutual fund schemes found in the database. Please populate schemes first.")
            self.stdout.write(self.style.SUCCESS(
                f"Fetching NAV history for all {schemes_to_process.count()} schemes using up to {MAX_WORKERS} parallel workers..."))
        elif options['scheme_codes']:
            schemes_to_process = MutualFundScheme.objects.filter(scheme_code__in=options['scheme_codes'])
            if not schemes_to_process.exists():
                raise CommandError(f"Could not find any schemes with codes: {options['scheme_codes']}")
        else:
            raise CommandError("No scheme codes specified. Provide scheme codes or use the --all flag.")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(self.fetch_for_scheme, scheme): scheme for scheme in schemes_to_process}

            for future in tqdm(as_completed(futures), total=len(schemes_to_process), desc="Fetching NAVs"):
                try:
                    future.result()
                except Exception as e:
                    scheme = futures[future]
                    self.stderr.write(self.style.ERROR(f"\nAn unexpected error occurred for scheme {scheme.scheme_code}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nNAV fetching complete."))

    def fetch_for_scheme(self, scheme):
        """
        This function contains the logic to fetch all historical NAVs for a *single* scheme.
        It is executed by a worker thread from the ThreadPoolExecutor.
        """
        today = datetime.date.today()
        # Get the last date we have NAV data for this scheme
        latest_nav = MutualFundNAV.objects.filter(scheme=scheme).order_by('-date').first()
        # Start fetching from the day after the latest record, or from a default start date (AMFI data is reliable from 2006)
        start_date = latest_nav.date + datetime.timedelta(days=1) if latest_nav else datetime.date(2006, 1, 1)

        current_start = start_date
        while current_start <= today:
            # AMFI allows fetching a maximum of 90 days of data at a time
            end_date = current_start + datetime.timedelta(days=89)
            if end_date > today:
                end_date = today

            params = {
                'SchemeCode': scheme.scheme_code,
                'FromDate': current_start.strftime('%d-%b-%Y'),
                'ToDate': end_date.strftime('%d-%b-%Y')
            }

            try:
                response = requests.get(AMFI_HISTORY_URL, params=params, timeout=15)
                response.raise_for_status()

                # If there's no text or AMFI returns its standard "no data" message, skip this period.
                if "No data found" in response.text or not response.text.strip():
                    current_start = end_date + datetime.timedelta(days=1)
                    continue

                lines = response.text.strip().split('\r\n')
                navs_to_create = []

                for line in lines:
                    # Skip headers or malformed lines. The header contains "Net Asset Value".
                    if not line or "Net Asset Value" in line:
                        continue
                    
                    parts = line.strip().split(';')
                    if len(parts) < 8:
                        continue

                    try:
                        # The standard AMFI format is: Scheme Code;...;Net Asset Value;...;Date
                        nav_value = Decimal(parts[4])
                        nav_date = datetime.datetime.strptime(parts[7], '%d-%b-%Y').date()

                        navs_to_create.append(
                            MutualFundNAV(scheme=scheme, date=nav_date, nav=nav_value)
                        )
                    except (InvalidOperation, ValueError, IndexError):
                        # This will catch errors from non-numeric NAVs, bad date formats, or incomplete lines
                        continue

                if navs_to_create:
                    MutualFundNAV.objects.bulk_create(navs_to_create, ignore_conflicts=True)

            except requests.exceptions.RequestException as e:
                # Log network errors but don't stop the entire process for this scheme
                self.stderr.write(self.style.WARNING(f"\nNetwork error for scheme {scheme.scheme_code} in range {current_start} to {end_date}: {e}"))
            
            # Move to the next 90-day period
            current_start = end_date + datetime.timedelta(days=1)
