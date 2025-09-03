import pandas as pd
import joblib
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from statsmodels.tsa.arima.model import ARIMA
from apps.securities.models import Security, SecurityPrice
from tqdm import tqdm
import warnings

# Define the directory to save trained models
MODEL_DIR = Path(settings.BASE_DIR) / "apps" / "analysis" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

class Command(BaseCommand):
    """
    Trains and saves a simple ARIMA model for one or all securities.
    """
    help = 'Trains a time-series forecasting model for specified security tickers or all of them.'

    def add_arguments(self, parser):
        parser.add_argument('tickers', nargs='*', type=str, help='Optional list of security tickers to train models for.')
        parser.add_argument('--all', action='store_true', help='Train models for all securities in the database.')

    def handle(self, *args, **options):
        if options['all']:
            securities = list(Security.objects.all())
        elif options['tickers']:
            securities = list(Security.objects.filter(ticker__in=[t.upper() for t in options['tickers']]))
        else:
            raise CommandError("No tickers specified. Use tickers or the --all flag.")

        if not securities:
            raise CommandError("No securities found for the given criteria.")

        self.stdout.write(f"Starting ARIMA model training for {len(securities)} securities...")

        # Suppress the specific ValueWarning from statsmodels for a cleaner bulk output
        warnings.filterwarnings("ignore", message="A date index has been provided, but it has no associated frequency information")

        for security in tqdm(securities, desc="Training ARIMA Models"):
            try:
                prices = SecurityPrice.objects.filter(security=security).order_by('date').values_list('date', 'close')
                if prices.count() < 100:
                    self.stderr.write(self.style.WARNING(f"Skipping {security.ticker}: Not enough data ({prices.count()} points)."))
                    continue

                # Ensure the index is a proper DatetimeIndex
                data = pd.Series(
                    [price[1] for price in prices],
                    index=pd.to_datetime([price[0] for price in prices]),
                    dtype=float
                )

                # ** THE DEFINITIVE FIX **
                # 1. Resample the data to a daily frequency ('D'). This creates a complete
                #    date range and introduces NaN for missing days (weekends/holidays).
                # 2. Forward-fill the missing values to carry the last known price over.
                # This provides the model with a regular, clean time series and resolves the warning.
                data = data.asfreq('D').fillna(method='ffill')

                # A simple ARIMA model configuration (p=5, d=1, q=0)
                model = ARIMA(data, order=(5, 1, 0))
                model_fit = model.fit()

                # Save the trained model
                model_path = MODEL_DIR / f'{security.ticker}_arima.joblib'
                joblib.dump(model_fit, str(model_path))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Skipping {security.ticker} due to an error: {e}"))
                continue

        self.stdout.write(self.style.SUCCESS("\nARIMA model training complete."))
