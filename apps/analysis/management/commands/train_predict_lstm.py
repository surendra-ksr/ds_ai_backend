import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from apps.securities.models import Security, SecurityPrice
from apps.analysis.models import Prediction
import datetime

# Number of past days of data to use for predicting the next day
SEQUENCE_LENGTH = 60

class Command(BaseCommand):
    help = 'Trains an LSTM model and generates future price predictions.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', type=str, help='The ticker symbol to model.')
        parser.add_argument('--days', type=int, default=5, help='Number of future days to predict.')

    def handle(self, *args, **options):
        ticker_symbol = options['ticker']
        forecast_days = options['days']

        self.stdout.write(f"Starting LSTM prediction for {ticker_symbol}...")

        try:
            security = Security.objects.get(ticker=ticker_symbol.split('.')[0])
        except Security.DoesNotExist:
            raise CommandError(f"Security {ticker_symbol} not found.")

        # 1. Data Loading and Preparation
        prices = SecurityPrice.objects.filter(security=security).order_by('date')
        if prices.count() < SEQUENCE_LENGTH:
            raise CommandError(f"Not enough data for {ticker_symbol}. Need at least {SEQUENCE_LENGTH} days.")

        df = pd.DataFrame.from_records(prices.values('date', 'adj_close', 'volume', 'sma_50', 'rsi'))
        df.set_index('date', inplace=True)
        df.fillna(method='ffill', inplace=True) # Fill any missing indicator values

        # 2. Preprocessing and Scaling
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df)

        # 3. Create Training Sequences
        x_train, y_train = [], []
        for i in range(SEQUENCE_LENGTH, len(scaled_data)):
            x_train.append(scaled_data[i-SEQUENCE_LENGTH:i, :])
            y_train.append(scaled_data[i, 0]) # Predicting the 'adj_close' price

        x_train, y_train = np.array(x_train), np.array(y_train)

        # 4. Model Architecture
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], x_train.shape[2])),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')

        # 5. Training
        self.stdout.write("Training LSTM model... (This can be time-consuming)")
        model.fit(x_train, y_train, batch_size=32, epochs=20) # Epochs can be increased for better accuracy

        # 6. Prediction
        self.stdout.write(self.style.SUCCESS("Model training complete. Generating forecast."))
        
        last_sequence = scaled_data[-SEQUENCE_LENGTH:]
        current_batch = np.reshape(last_sequence, (1, SEQUENCE_LENGTH, x_train.shape[2]))
        
        future_predictions = []
        for i in range(forecast_days):
            # Predict the next value
            next_prediction = model.predict(current_batch)[0]
            future_predictions.append(next_prediction[0])
            
            # Create a new sequence for the next prediction
            new_row = np.append(current_batch[0, -1, 1:], next_prediction) # Append predicted price, shift others
            new_sequence = np.append(current_batch[0, 1:, :], [new_row], axis=0)
            current_batch = np.reshape(new_sequence, (1, SEQUENCE_LENGTH, x_train.shape[2]))

        # Inverse transform to get actual price values
        # We need to create a dummy array with the same shape as the scaler expects
        dummy_array = np.zeros((len(future_predictions), df.shape[1]))
        dummy_array[:, 0] = future_predictions
        actual_predictions = scaler.inverse_transform(dummy_array)[:, 0]

        # 7. Saving Results
        last_date = df.index[-1]
        for i in range(forecast_days):
            prediction_date = last_date.date() + datetime.timedelta(days=i + 1)
            Prediction.objects.update_or_create(
                security=security,
                model_name='LSTM',
                prediction_date=prediction_date,
                defaults={'predicted_value': actual_predictions[i]}
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully saved {forecast_days} LSTM predictions for {ticker_symbol}."))
