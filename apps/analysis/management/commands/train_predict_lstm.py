import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler

from apps.analysis.data_processing import prepare_lstm_data

# Define the directory to save trained models and scalers
MODEL_DIR = Path(settings.BASE_DIR) / "apps" / "analysis" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# --- Model & Training Configuration ---
SEQUENCE_LENGTH = 60
EPOCHS = 50
BATCH_SIZE = 32

class Command(BaseCommand):
    """
    Trains and saves an LSTM model for a given security, including sentiment analysis features.
    """
    help = 'Trains an LSTM forecasting model for a specified security ticker.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', type=str, help='The ticker symbol of the security to train a model for.')

    def handle(self, *args, **options):
        ticker = options['ticker'].upper()

        self.stdout.write(f"Preparing data for {ticker}...")
        df = prepare_lstm_data(ticker)

        if df is None or df.empty:
            raise CommandError(f"Could not prepare data for {ticker}. Not enough data points or security does not exist.")

        # The target variable we want to predict
        target_column = 'close'
        # Drop non-numeric columns if any exist before scaling
        df = df.select_dtypes(include=np.number)

        # --- Data Scaling ---
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df)

        # Save the scaler for this ticker
        scaler_path = MODEL_DIR / f'{ticker}_lstm_scaler.joblib'
        # Convert Path to string for cross-platform compatibility
        joblib.dump(scaler, str(scaler_path))
        self.stdout.write(self.style.SUCCESS(f"Scaler saved to {scaler_path}"))

        # --- Sequence Creation ---
        X, y = [], []
        for i in range(SEQUENCE_LENGTH, len(scaled_data)):
            X.append(scaled_data[i-SEQUENCE_LENGTH:i])
            # The target is the 'close' price, get its index
            target_col_index = df.columns.get_loc(target_column)
            y.append(scaled_data[i, target_col_index])

        X, y = np.array(X), np.array(y)

        self.stdout.write(f"Created {X.shape[0]} sequences of length {X.shape[1]}.")

        # --- LSTM Model Architecture ---
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1)
        ])

        model.compile(optimizer='adam', loss='mean_squared_error')
        model.summary()

        # --- Model Training ---
        self.stdout.write(f"Training LSTM model for {ticker}...")
        model.fit(X, y, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=1)

        # --- Saving the Model ---
        model_path = MODEL_DIR / f'{ticker}_lstm_model.h5'
        model.save(str(model_path)) # Convert Path to string

        self.stdout.write(self.style.SUCCESS(f'Successfully trained and saved LSTM model for {ticker} to {model_path}'))
