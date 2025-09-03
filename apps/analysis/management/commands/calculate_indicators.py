import pandas as pd
import pandas_ta as ta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.securities.models import Security, SecurityPrice

class Command(BaseCommand):
    help = 'Calculates technical indicators for specified securities or all securities.'

    def add_arguments(self, parser):
        parser.add_argument('tickers', nargs='*', type=str, help='Optional list of ticker symbols to process.')
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all securities in the database.',
        )

    def handle(self, *args, **options):
        tickers_to_process = options['tickers']
        if options['all']:
            self.stdout.write(self.style.SUCCESS("Processing all securities in the database..."))
            securities = Security.objects.all()
        elif tickers_to_process:
            securities = Security.objects.filter(ticker__in=[t.split('.')[0] for t in tickers_to_process])
        else:
            raise CommandError("No securities specified. Provide tickers or use the --all flag.")

        for security in securities:
            self.stdout.write(f"--- Calculating indicators for {security.ticker} ---")
            
            # Fetch all prices for the security, ordered by date ascending
            prices = SecurityPrice.objects.filter(security=security).order_by('date')
            if prices.count() < 20: # Need at least 20 days for SMA_20
                self.stdout.write(self.style.WARNING("  - Not enough price data. Skipping."))
                continue

            # Create a pandas DataFrame
            df = pd.DataFrame.from_records(prices.values('id', 'date', 'open', 'high', 'low', 'close', 'volume'))
            df.set_index('date', inplace=True)
            df.rename(columns=lambda x: x.capitalize(), inplace=True)

            # Calculate indicators using pandas-ta
            df.ta.sma(length=20, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.sma(length=200, append=True)
            df.ta.rsi(append=True)
            df.ta.macd(append=True)
            df.ta.bbands(append=True)

            # Prepare for bulk update
            with transaction.atomic():
                price_map = {p.id: p for p in prices}
                fields_to_update = [
                    'sma_20', 'sma_50', 'sma_200', 'rsi',
                    'macd', 'bollinger_upper', 'bollinger_lower'
                ]
                
                for index, row in df.iterrows():
                    price_obj = price_map.get(row['id'])
                    if price_obj:
                        price_obj.sma_20 = row.get('SMA_20')
                        price_obj.sma_50 = row.get('SMA_50')
                        price_obj.sma_200 = row.get('SMA_200')
                        price_obj.rsi = row.get('RSI_14')
                        price_obj.macd = row.get('MACDh_12_26_9')
                        price_obj.bollinger_upper = row.get('BBU_20_2.0')
                        price_obj.bollinger_lower = row.get('BBL_20_2.0')

                SecurityPrice.objects.bulk_update(list(price_map.values()), fields_to_update, batch_size=100)

            self.stdout.write(self.style.SUCCESS(f"  - Successfully calculated and stored indicators."))
