import yfinance as yf
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from apps.securities.models import Security, Exchange, SecurityPrice
from apps.core.models import Category
from apps.securities.data.nifty_500_tickers import NIFTY_50, NIFTY_NEXT_50, MAJOR_STOCKS

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

        nse_exchange, _ = Exchange.objects.get_or_create(name='NSE', defaults={'currency': 'INR'})
        nifty50_cat, _ = Category.objects.get_or_create(name="Nifty 50")
        nifty_next50_cat, _ = Category.objects.get_or_create(name="Nifty Next 50")

        # Wrap the main loop with tqdm for a progress bar
        for ticker_symbol in tqdm(tickers_to_fetch, desc="Fetching Stock Prices"):
            try:
                security, created = Security.objects.get_or_create(
                    ticker=ticker_symbol.split('.')[0],
                    exchange=nse_exchange,
                    defaults={'name': ticker_symbol}
                )

                if created:
                    if ticker_symbol in NIFTY_50:
                        security.categories.add(nifty50_cat)
                    elif ticker_symbol in NIFTY_NEXT_50:
                        security.categories.add(nifty_next50_cat)

                ticker_obj = yf.Ticker(ticker_symbol)
                hist = ticker_obj.history(period="max", auto_adjust=False)

                if hist.empty:
                    continue

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

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"\nFailed to process {ticker_symbol}. Error: {e}"))

        self.stdout.write(self.style.SUCCESS("\nPrice fetching complete."))
