import pandas as pd
import joblib
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from statsmodels.tsa.arima.model import ARIMA
from apps.securities.models import Security, SecurityPrice

# Define the directory to save trained models
MODEL_DIR = Path(settings.BASE_DIR) / "apps" / "analysis" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

class Command(BaseCommand):
    """
    Trains and saves a simple ARIMA model for a given security.
    """
    help = 'Trains a time-series forecasting model for a specified security ticker.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', type=str, help='The ticker symbol of the security to train a model for.')

    def handle(self, *args, **options):
        ticker = options['ticker'].upper()

        try:
            security = Security.objects.get(ticker=ticker)
        except Security.DoesNotExist:
            raise CommandError(f'Security with ticker "{ticker}" does not exist.')

        # Fetch historical data
        prices = SecurityPrice.objects.filter(security=security).order_by('date').values_list('date', 'close')
        if prices.count() < 100: # Need sufficient data for training
            raise CommandError(f'Not enough historical data for "{ticker}" to train a model (found {prices.count()} data points).')

        self.stdout.write(f"Found {prices.count()} data points for {ticker}. Preparing data...")
        
        # Convert to a pandas Series
        data = pd.Series([price[1] for price in prices], index=[price[0] for price in prices])
        data = data.astype(float)

        self.stdout.write("Training ARIMA(5,1,0) model...")

        try:
            # A simple ARIMA model configuration (p=5, d=1, q=0)
            model = ARIMA(data, order=(5, 1, 0))
            model_fit = model.fit()

            # Save the trained model
            model_path = MODEL_DIR / f'{ticker}_arima.joblib'
            # Convert Path to string for cross-platform compatibility with joblib
            joblib.dump(model_fit, str(model_path))

        except Exception as e:
            raise CommandError(f"An error occurred during model training: {e}")

        self.stdout.write(self.style.SUCCESS(f'Successfully trained and saved ARIMA model for {ticker} to {model_path}'))
