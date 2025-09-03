import yfinance as yf
import numpy as np
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from apps.securities.models import Security, SecurityPriceIntraday

class Command(BaseCommand):
    """This command fetches recent intraday price data, respecting API limitations and validating data types."""
    help = 'Fetches recent intraday (1-minute interval) price data for the last 7 days for one or all stocks.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', type=str, help='Optional ticker symbol to fetch intraday data for.')
        parser.add_argument('--all', action='store_true', help='Fetch intraday data for all securities in the database.')

    def handle(self, *args, **options):
        securities_to_process = []
        is_bulk = options['all']

        if is_bulk:
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
            self.fetch_for_security(security, is_bulk)

    def fetch_for_security(self, security, is_bulk):
        try:
            data = yf.download(tickers=f"{security.ticker}.NS", period="7d", interval="1m", auto_adjust=False, progress=False)

            if data.empty:
                if not is_bulk:
                    self.stdout.write(self.style.WARNING("No intraday data found for this ticker."))
                return

            successful_rows = 0
            for index, row in data.iterrows():
                # --- CRITICAL FIX: Validate that all price data are numbers before saving ---
                open_price = row.get('Open')
                high_price = row.get('High')
                low_price = row.get('Low')
                close_price = row.get('Close')
                volume = row.get('Volume')

                if not all(isinstance(price, (int, float, np.number)) for price in [open_price, high_price, low_price, close_price, volume]):
                    continue # Skip this invalid row

                SecurityPriceIntraday.objects.update_or_create(
                    security=security,
                    datetime=index.to_pydatetime(),
                    defaults={
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'volume': volume
                    }
                )
                successful_rows += 1

            if not is_bulk and successful_rows > 0:
                self.stdout.write(self.style.SUCCESS(f"Successfully stored {successful_rows} valid intraday data points."))

        except Exception as e:
            if not is_bulk:
                raise CommandError(f"An error occurred while fetching intraday data for {security.ticker}. Error: {e}")
            else:
                pass
