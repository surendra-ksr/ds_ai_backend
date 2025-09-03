import yfinance as yf
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from apps.securities.models import Security, SecurityPriceIntraday

class Command(BaseCommand):
    """This command fetches recent intraday price data, respecting API limitations."""
    help = 'Fetches recent intraday (1-minute interval) price data for the last 7 days for one or all stocks.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', type=str, help='Optional ticker symbol to fetch intraday data for.')
        parser.add_argument('--all', action='store_true', help='Fetch intraday data for all securities in the database.')

    def handle(self, *args, **options):
        securities_to_process = []
        if options['all']:
            securities_to_process = Security.objects.all()
            self.stdout.write(self.style.SUCCESS(f"Fetching last 7 days of intraday data for all {securities_to_process.count()} securities..."))
        elif options['ticker']:
            try:
                security = Security.objects.get(ticker=options['ticker'].split('.')[0])
                securities_to_process.append(security)
            except Security.DoesNotExist:
                raise CommandError(f"Security {options['ticker']} not found.")
        else:
            raise CommandError("No ticker specified. Provide a ticker or use the --all flag.")

        for security in tqdm(securities_to_process, desc="Fetching Intraday Prices"):
            self.fetch_for_security(security)

    def fetch_for_security(self, security):
        try:
            # --- CRITICAL FIX: Request a 7-day period to respect API limits ---
            data = yf.download(tickers=f"{security.ticker}.NS", period="7d", interval="1m", auto_adjust=False, progress=False)

            if data.empty:
                return

            for index, row in data.iterrows():
                SecurityPriceIntraday.objects.update_or_create(
                    security=security,
                    datetime=index.to_pydatetime(),
                    defaults={
                        'open': row['Open'],
                        'high': row['High'],
                        'low': row['Low'],
                        'close': row['Close'],
                        'volume': row['Volume']
                    }
                )
        except Exception:
            # Some tickers might not have intraday data, or other API errors can occur. Silently continue.
            pass
