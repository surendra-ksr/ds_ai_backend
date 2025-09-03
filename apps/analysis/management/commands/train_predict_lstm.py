import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

from apps.analysis.data_processing import prepare_lstm_data
from apps.securities.models import Security

# Define the directory to save trained models and scalers
MODEL_DIR = Path(settings.BASE_DIR) / "apps" / "analysis" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# --- Model & Training Configuration ---
SEQUENCE_LENGTH = 60
EPOCHS = 50
BATCH_SIZE = 32

class Command(BaseCommand):
    """
    Trains and saves an LSTM model for one or all securities.
    """
    help = 'Trains an LSTM forecasting model for specified security tickers or all of them.'

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

        self.stdout.write(f"Starting LSTM model training for {len(securities)} securities...")

        for security in tqdm(securities, desc="Training LSTM Models"):
            try:
                df = prepare_lstm_data(security.ticker)
                if df is None or df.empty:
                    self.stderr.write(self.style.WARNING(f"Skipping {security.ticker}: Not enough data to prepare features."))
                    continue

                target_column = 'close'
                df = df.select_dtypes(include=np.number)

                scaler = MinMaxScaler(feature_range=(0, 1))
                scaled_data = scaler.fit_transform(df)

                scaler_path = MODEL_DIR / f'{security.ticker}_lstm_scaler.joblib'
                joblib.dump(scaler, str(scaler_path))

                X, y = [], []
                for i in range(SEQUENCE_LENGTH, len(scaled_data)):
                    X.append(scaled_data[i-SEQUENCE_LENGTH:i])
                    target_col_index = df.columns.get_loc(target_column)
                    y.append(scaled_data[i, target_col_index])

                X, y = np.array(X), np.array(y)

                if X.shape[0] == 0:
                    self.stderr.write(self.style.WARNING(f"Skipping {security.ticker}: Not enough data to create sequences."))
                    continue

                model = Sequential([
                    LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
                    Dropout(0.2),
                    LSTM(units=50, return_sequences=False),
                    Dropout(0.2),
                    Dense(units=25),
                    Dense(units=1)
                ])
                model.compile(optimizer='adam', loss='mean_squared_error')
                model.fit(X, y, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=0) # Set verbose=0 for cleaner bulk output

                model_path = MODEL_DIR / f'{security.ticker}_lstm_model.h5'
                model.save(str(model_path))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Skipping {security.ticker} due to an error: {e}"))
                continue

        self.stdout.write(self.style.SUCCESS("\nLSTM model training complete."))
