import requests
import datetime
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from apps.mutual_funds.models import MutualFundScheme, MutualFundNAV

AMFI_HISTORY_URL = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"

class Command(BaseCommand):
    help = 'Fetches historical NAV data for one or all mutual fund schemes.'

    def add_arguments(self, parser):
        parser.add_argument('scheme_codes', nargs='*', type=int, help='Optional list of AMFI scheme codes to fetch.')
        parser.add_argument('--all', action='store_true', help='Fetch NAV history for all schemes in the database.')

    def handle(self, *args, **options):
        schemes_to_process = []
        if options['all']:
            schemes_to_process = MutualFundScheme.objects.all()
            self.stdout.write(self.style.SUCCESS(f"Fetching NAV history for all {schemes_to_process.count()} schemes..."))
        elif options['scheme_codes']:
            schemes_to_process = MutualFundScheme.objects.filter(scheme_code__in=options['scheme_codes'])
        else:
            raise CommandError("No scheme codes specified. Provide scheme codes or use the --all flag.")

        for scheme in tqdm(schemes_to_process, desc="Fetching NAVs"):
            self.fetch_for_scheme(scheme)

        self.stdout.write(self.style.SUCCESS("\nNAV fetching complete."))

    def fetch_for_scheme(self, scheme):
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
                response = requests.get(AMFI_HISTORY_URL, params=params)
                response.raise_for_status()

                if "No data found" in response.text or not response.text.strip():
                    current_start = end_date + datetime.timedelta(days=1)
                    continue

                lines = response.text.strip().split('\r\n')
                navs_to_create = []
                for line in lines:
                    if ';' not in line or not parts[0].isdigit(): continue
                    parts = line.strip().split(';')
                    if len(parts) < 8: continue

                    nav_date = datetime.datetime.strptime(parts[7], '%d-%b-%Y').date()
                    nav_value = float(parts[4])
                    navs_to_create.append(MutualFundNAV(scheme=scheme, date=nav_date, nav=nav_value))
                
                if navs_to_create:
                    MutualFundNAV.objects.bulk_create(navs_to_create, ignore_conflicts=True)

            except Exception:
                # Silently continue on error to not interrupt the bulk process
                pass
            
            current_start = end_date + datetime.timedelta(days=1)
