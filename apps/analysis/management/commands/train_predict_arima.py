import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from statsmodels.tsa.arima.model import ARIMA
from apps.securities.models import Security, SecurityPrice
from apps.analysis.models import Prediction
import datetime

class Command(BaseCommand):
    help = 'Trains an ARIMA model and generates future price predictions for a security.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', type=str, help='The ticker symbol of the security to model.')
        parser.add_argument('--days', type=int, default=5, help='Number of future days to predict.')

    def handle(self, *args, **options):
        ticker_symbol = options['ticker']
        forecast_days = options['days']

        self.stdout.write(f"Starting ARIMA prediction for {ticker_symbol} for {forecast_days} days.")

        try:
            security = Security.objects.get(ticker=ticker_symbol.split('.')[0])
        except Security.DoesNotExist:
            raise CommandError(f"Security {ticker_symbol} not found.")

        # Fetch historical data
        prices = SecurityPrice.objects.filter(security=security).order_by('date').values_list('date', 'adj_close')
        if prices.count() < 50: # Need sufficient data for the model
            raise CommandError(f"Not enough historical data for {ticker_symbol} to build a model.")

        # Create a pandas Series of adjusted close prices
        ts_data = pd.Series([p[1] for p in prices], index=[p[0] for p in prices])

        self.stdout.write("Training ARIMA model... (This may take a moment)")

        try:
            # Fit the ARIMA model. A common starting point for stock data is (5,1,0).
            # p=5: Lags from the past 5 days
            # d=1: Difference to make the series stationary
            # q=0: No moving average window
            model = ARIMA(ts_data, order=(5, 1, 0))
            model_fit = model.fit()

            # Generate forecast
            forecast = model_fit.forecast(steps=forecast_days)

            self.stdout.write(self.style.SUCCESS("Model training complete. Saving predictions."))

            # Save predictions to the database
            last_date = ts_data.index[-1]
            for i in range(forecast_days):
                prediction_date = last_date + datetime.timedelta(days=i + 1)
                predicted_value = forecast.iloc[i]

                Prediction.objects.update_or_create(
                    security=security,
                    model_name='ARIMA',
                    prediction_date=prediction_date,
                    defaults={'predicted_value': predicted_value}
                )
            
            self.stdout.write(self.style.SUCCESS(f"Successfully saved {forecast_days} predictions for {ticker_symbol}."))

        except Exception as e:
            raise CommandError(f"An error occurred during model training or prediction: {e}")
