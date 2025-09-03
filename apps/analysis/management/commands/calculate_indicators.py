import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tqdm import tqdm
from apps.securities.models import Security, SecurityPrice

# --- Manual Technical Indicator Functions ---

def calculate_sma(series, length=20):
    return series.rolling(window=length).mean()

def calculate_rsi(series, length=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def calculate_bbands(series, length=20, std_dev=2.0):
    middle_band = calculate_sma(series, length)
    std = series.rolling(window=length).std()
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    return upper_band, lower_band

class Command(BaseCommand):
    help = 'Calculates technical indicators for all securities using manual pandas functions.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Process all securities in the database.')

    def handle(self, *args, **options):
        if not options['all']:
            raise CommandError("This command now only supports the --all flag.")

        self.stdout.write(self.style.SUCCESS("Processing all securities in the database..."))
        securities = Security.objects.all()

        for security in tqdm(securities, desc="Calculating Indicators"):
            prices = SecurityPrice.objects.filter(security=security).order_by('date')
            if prices.count() < 200:
                continue

            df = pd.DataFrame.from_records(prices.values('id', 'date', 'close'))
            df.set_index('date', inplace=True)

            # --- Apply Manual Calculations ---
            df['sma_20'] = calculate_sma(df['close'], 20)
            df['sma_50'] = calculate_sma(df['close'], 50)
            df['sma_200'] = calculate_sma(df['close'], 200)
            df['rsi'] = calculate_rsi(df['close'])
            df['macd'], _ = calculate_macd(df['close'])
            df['bollinger_upper'], df['bollinger_lower'] = calculate_bbands(df['close'])

            # --- Update Database ---
            with transaction.atomic():
                price_map = {p.id: p for p in prices}
                fields_to_update = [
                    'sma_20', 'sma_50', 'sma_200', 'rsi',
                    'macd', 'bollinger_upper', 'bollinger_lower'
                ]
                
                for index, row in df.iterrows():
                    price_obj = price_map.get(row['id'])
                    if price_obj:
                        # --- CRITICAL FIX: Explicitly check for NaN and convert to None ---
                        price_obj.sma_20 = None if pd.isna(row.get('sma_20')) else row.get('sma_20')
                        price_obj.sma_50 = None if pd.isna(row.get('sma_50')) else row.get('sma_50')
                        price_obj.sma_200 = None if pd.isna(row.get('sma_200')) else row.get('sma_200')
                        price_obj.rsi = None if pd.isna(row.get('rsi')) else row.get('rsi')
                        price_obj.macd = None if pd.isna(row.get('macd')) else row.get('macd')
                        price_obj.bollinger_upper = None if pd.isna(row.get('bollinger_upper')) else row.get('bollinger_upper')
                        price_obj.bollinger_lower = None if pd.isna(row.get('bollinger_lower')) else row.get('bollinger_lower')

                SecurityPrice.objects.bulk_update(list(price_map.values()), fields_to_update, batch_size=500)

        self.stdout.write(self.style.SUCCESS("\nIndicator calculation complete."))
