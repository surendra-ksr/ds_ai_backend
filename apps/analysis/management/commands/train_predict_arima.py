import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from statsmodels.tsa.arima.model import ARIMA
from tqdm import tqdm
from apps.securities.models import Security, SecurityPrice
from apps.analysis.models import Prediction
import datetime
import warnings

# Suppress the specific, known warnings from statsmodels to keep the output clean
warnings.filterwarnings("ignore", message="A date index has been provided, but it has no associated frequency information")
warnings.filterwarnings("ignore", message="No supported index is available. Prediction results will be given with an integer index beginning at `start`.")

class Command(BaseCommand):
    """This command trains an ARIMA model and generates future price predictions."""
    help = 'Trains an ARIMA model and generates future price predictions for one or all securities.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', type=str, help='Optional ticker symbol to model.')
        parser.add_argument('--all', action='store_true', help='Generate predictions for all securities.')
        parser.add_argument('--days', type=int, default=5, help='Number of future days to predict.')

    def handle(self, *args, **options):
        forecast_days = options['days']
        securities_to_process = []

        if options['all']:
            securities_to_process = Security.objects.all()
            self.stdout.write(self.style.SUCCESS(f"Generating ARIMA predictions for all {securities_to_process.count()} securities..."))
        elif options['ticker']:
            try:
                security = Security.objects.get(ticker=options['ticker'].split('.')[0])
                securities_to_process.append(security)
            except Security.DoesNotExist:
                raise CommandError(f"Security {options['ticker']} not found.")
        else:
            raise CommandError("No ticker specified. Provide a ticker or use the --all flag.")

        for security in tqdm(securities_to_process, desc="ARIMA Predictions"):
            self.predict_for_security(security, forecast_days)

    def predict_for_security(self, security, forecast_days):
        prices = SecurityPrice.objects.filter(security=security).order_by('date').values_list('date', 'adj_close')
        if prices.count() < 50:
            return

        # --- CRITICAL FIX: Create a pandas Series with a proper DatetimeIndex and set frequency ---
        dates = [p[0] for p in prices]
        values = [float(p[1]) for p in prices]
        ts_data = pd.Series(values, index=pd.to_datetime(dates))
        # Use 'B' for Business Day frequency. Forward-fill missing values (holidays).
        ts_data = ts_data.asfreq('B', method='ffill')

        try:
            model = ARIMA(ts_data, order=(5, 1, 0))
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=forecast_days)

            last_date = ts_data.index[-1]
            # Generate future dates based on the business day frequency
            future_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days)

            for i in range(forecast_days):
                Prediction.objects.update_or_create(
                    security=security,
                    model_name='ARIMA',
                    prediction_date=future_dates[i].date(),
                    defaults={'predicted_value': forecast.iloc[i]}
                )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"\nCould not generate ARIMA prediction for {security.ticker}. Error: {e}"))
