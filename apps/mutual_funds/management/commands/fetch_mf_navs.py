import requests
import datetime
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from apps.mutual_funds.models import MutualFundScheme, MutualFundNAV

AMFI_HISTORY_URL = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"

class Command(BaseCommand):
    help = 'Fetches historical NAV data for specified mutual fund schemes.'

    def add_arguments(self, parser):
        parser.add_argument('scheme_codes', nargs='+', type=int, help='A list of AMFI scheme codes to fetch NAV history for.')

    def handle(self, *args, **options):
        scheme_codes = options['scheme_codes']
        today = datetime.date.today()

        # Wrap the main loop with tqdm for a progress bar
        for scheme_code in tqdm(scheme_codes, desc="Fetching NAVs"):
            try:
                scheme = MutualFundScheme.objects.get(scheme_code=scheme_code)
            except MutualFundScheme.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"\nScheme with code {scheme_code} not found. Skipping."))
                continue

            latest_nav = MutualFundNAV.objects.filter(scheme=scheme).order_by('-date').first()
            start_date = latest_nav.date + datetime.timedelta(days=1) if latest_nav else datetime.date(2000, 1, 1)

            current_start = start_date
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

                        nav_date_str = parts[7]
                        nav_value = parts[4]
                        nav_date = datetime.datetime.strptime(nav_date_str, '%d-%b-%Y').date()

                        navs_to_create.append(
                            MutualFundNAV(scheme=scheme, date=nav_date, nav=float(nav_value))
                        )
                    
                    if navs_to_create:
                        MutualFundNAV.objects.bulk_create(navs_to_create, ignore_conflicts=True)

                except requests.exceptions.RequestException as e:
                    self.stderr.write(self.style.ERROR(f"\nHTTP Error for {scheme_code}: {e}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"\nAn error occurred processing NAV data for {scheme_code}: {e}"))

                current_start = end_date + datetime.timedelta(days=1)

        self.stdout.write(self.style.SUCCESS("\nNAV fetching complete."))
