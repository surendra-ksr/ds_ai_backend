import requests
import datetime
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from apps.mutual_funds.models import MutualFundScheme, MutualFundNAV

AMFI_HISTORY_URL = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"

# Define the number of parallel workers for fetching. 10 is a safe default.
MAX_WORKERS = 10

class Command(BaseCommand):
    """This command fetches historical NAV data for mutual funds, using a thread pool for concurrency."""
    help = 'Fetches historical NAV data for one or all mutual fund schemes concurrently.'

    def add_arguments(self, parser):
        parser.add_argument('scheme_codes', nargs='*', type=int, help='Optional list of AMFI scheme codes to fetch.')
        parser.add_argument('--all', action='store_true', help='Fetch NAV history for all schemes in the database.')

    def handle(self, *args, **options):
        schemes_to_process = []
        if options['all']:
            schemes_to_process = MutualFundScheme.objects.all()
            self.stdout.write(self.style.SUCCESS(f"Fetching NAV history for all {schemes_to_process.count()} schemes using up to {MAX_WORKERS} parallel workers..."))
        elif options['scheme_codes']:
            schemes_to_process = MutualFundScheme.objects.filter(scheme_code__in=options['scheme_codes'])
        else:
            raise CommandError("No scheme codes specified. Provide scheme codes or use the --all flag.")

        # Use a ThreadPoolExecutor to run fetches in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(self.fetch_for_scheme, scheme): scheme for scheme in schemes_to_process}
            
            # as_completed yields futures as they finish, which is perfect for a progress bar
            for future in tqdm(as_completed(futures), total=len(schemes_to_process), desc="Fetching NAVs"):
                try:
                    future.result() # We call result() to raise any exceptions that occurred in the thread
                except Exception as e:
                    scheme = futures[future]
                    self.stderr.write(self.style.ERROR(f"\nAn error occurred for scheme {scheme.scheme_code}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nNAV fetching complete."))

    def fetch_for_scheme(self, scheme):
        """
        This function contains the logic to fetch all historical NAVs for a *single* scheme.
        It is executed by a worker thread from the ThreadPoolExecutor.
        """
        today = datetime.date.today()
        latest_nav = MutualFundNAV.objects.filter(scheme=scheme).order_by('-date').first()
        start_date = latest_nav.date + datetime.timedelta(days=1) if latest_nav else datetime.date(2000, 1, 1)

        current_start = start_date
        while current_start <= today:
            end_date = current_start + datetime.timedelta(days=89)
            if end_date > today:
                end_date = today

            params = {
                'SchemeCode': scheme.scheme_code,
                'FromDate': current_start.strftime('%d-%b-%Y'),
                'ToDate': end_date.strftime('%d-%b-%Y')
            }

            try:
                response = requests.get(AMFI_HISTORY_URL, params=params, timeout=10)
                response.raise_for_status()

                if "No data found" in response.text or not response.text.strip():
                    current_start = end_date + datetime.timedelta(days=1)
                    continue

                lines = response.text.strip().split('\r\n')
                navs_to_create = []
                for line in lines:
                    parts = line.strip().split(';')
                    if len(parts) < 8 or not parts[0].isdigit(): continue
                    
                    nav_date = datetime.datetime.strptime(parts[7], '%d-%b-%Y').date()
                    nav_value = float(parts[4])
                    navs_to_create.append(MutualFundNAV(scheme=scheme, date=nav_date, nav=nav_value))
                
                if navs_to_create:
                    MutualFundNAV.objects.bulk_create(navs_to_create, ignore_conflicts=True)

            except requests.exceptions.RequestException:
                pass # Silently continue on network errors
            
            current_start = end_date + datetime.timedelta(days=1)
