import yfinance as yf
from django.core.management.base import BaseCommand, CommandError
from securities.models import Security, Exchange, SecurityPrice
from core.models import Category
from securities.data.nifty_500_tickers import NIFTY_50, NIFTY_NEXT_50, MAJOR_STOCKS

class Command(BaseCommand):
    help = 'Fetches historical OHLCV data for stocks. Can fetch specified tickers or all major stocks.'

    def add_arguments(self, parser):
        parser.add_argument('tickers', nargs='*', type=str, help='Optional list of ticker symbols to fetch.')
        parser.add_argument(
            '--all-major',
            action='store_true',
            help='Fetch data for all major stocks defined in the Nifty lists.',
        )

    def handle(self, *args, **options):
        tickers_to_fetch = options['tickers']
        if options['all_major']:
            self.stdout.write(self.style.SUCCESS("Fetching all major stocks..."))
            tickers_to_fetch = MAJOR_STOCKS
        
        if not tickers_to_fetch:
            raise CommandError("No tickers specified. Provide tickers or use the --all-major flag.")

        # Get or create the exchange
        nse_exchange, _ = Exchange.objects.get_or_create(name='NSE', defaults={'currency': 'INR'})

        # Get category objects
        nifty50_cat, _ = Category.objects.get_or_create(name="Nifty 50")
        nifty_next50_cat, _ = Category.objects.get_or_create(name="Nifty Next 50")

        for ticker_symbol in tickers_to_fetch:
            self.stdout.write(f"--- Processing {ticker_symbol} ---")

            try:
                # Find or create the security
                security, created = Security.objects.get_or_create(
                    ticker=ticker_symbol.split('.')[0],
                    exchange=nse_exchange,
                    defaults={'name': ticker_symbol}
                )

                if created:
                    self.stdout.write(f"  - Created new security: {security}")
                    # Assign category on creation
                    if ticker_symbol in NIFTY_50:
                        security.categories.add(nifty50_cat)
                        self.stdout.write(f"  - Assigned to category: Nifty 50")
                    elif ticker_symbol in NIFTY_NEXT_50:
                        security.categories.add(nifty_next50_cat)
                        self.stdout.write(f"  - Assigned to category: Nifty Next 50")

                # Fetch data from yfinance
                ticker_obj = yf.Ticker(ticker_symbol)
                hist = ticker_obj.history(period="max", auto_adjust=False)

                if hist.empty:
                    self.stdout.write(self.style.WARNING("  - No data found. Skipping price download."))
                    continue

                # Use update_or_create to be idempotent and avoid duplicates
                for index, row in hist.iterrows():
                    SecurityPrice.objects.update_or_create(
                        security=security,
                        date=index.date(),
                        defaults={
                            'open': row['Open'],
                            'high': row['High'],
                            'low': row['Low'],
                            'close': row['Close'],
                            'adj_close': row['Adj Close'],
                            'volume': row['Volume']
                        }
                    )

                self.stdout.write(self.style.SUCCESS(f"  - Successfully processed and stored {len(hist)} price points."))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to process {ticker_symbol}. Error: {e}"))
