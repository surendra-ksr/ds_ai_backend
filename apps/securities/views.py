from django.utils import timezone
from datetime import timedelta
from django.views.generic import TemplateView, ListView
from django.conf import settings
from rest_framework import viewsets, mixins, generics
from rest_framework.decorators import action
from rest_framework.response import Response
import pandas as pd
import pandas_ta as ta
import joblib
from pathlib import Path
import numpy as np
from tensorflow.keras.models import load_model

from apps.analysis.data_processing import prepare_lstm_data
from .models import Security, SecurityPrice, SecurityPriceIntraday, NewsArticle
from apps.users.models import Watchlist
from .serializers import (
    SecurityListSerializer, 
    SecurityDetailSerializer, 
    SecurityPriceIntradaySerializer,
    SecurityPriceSerializer,
    NewsArticleSerializer
)

# Define the directory where trained models are stored
MODEL_DIR = Path(settings.BASE_DIR) / "apps" / "analysis" / "models"

# --- API Views ---

class SecurityViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    """
    A ViewSet for listing and retrieving securities.
    Includes custom actions for technical analysis, news, and predictions.
    """
    queryset = Security.objects.all()
    lookup_field = 'ticker'

    def get_serializer_class(self):
        if self.action == 'list':
            return SecurityListSerializer
        if self.action == 'news':
            return NewsArticleSerializer
        return SecurityDetailSerializer

    @action(detail=True, methods=['get'])
    def analysis(self, request, ticker=None):
        security = self.get_object()
        prices = SecurityPrice.objects.filter(security=security).order_by('date')
        if not prices.exists():
            return Response({"detail": "No historical price data found."}, status=404)
        df = pd.DataFrame.from_records(prices.values('date', 'open', 'high', 'low', 'close', 'volume'))
        df.set_index('date', inplace=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.reset_index(inplace=True)
        analysis_data = df.where(pd.notnull(df), None).to_dict(orient='records')
        return Response(analysis_data)

    @action(detail=True, methods=['get'])
    def news(self, request, ticker=None):
        security = self.get_object()
        news_articles = NewsArticle.objects.filter(security=security).order_by('-published_at')
        page = self.paginate_queryset(news_articles)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(news_articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def predict(self, request, ticker=None):
        security = self.get_object()
        model_path = MODEL_DIR / f'{security.ticker}_arima.joblib'
        if not model_path.exists():
            return Response({"detail": "No trained model found for this security."}, status=404)
        try:
            model_fit = joblib.load(model_path)
            forecast = model_fit.get_forecast(steps=1)
            predicted_value = forecast.predicted_mean.iloc[0]
            conf_int = forecast.conf_int().iloc[0]
            last_price = SecurityPrice.objects.filter(security=security).latest('date').close
            trend = "Up" if predicted_value > last_price else "Down" if predicted_value < last_price else "Neutral"
            return Response({
                'ticker': security.ticker,
                'last_close': float(last_price),
                'predicted_value': float(predicted_value),
                'confidence_interval': [float(conf_int[0]), float(conf_int[1])],
                'trend': trend,
                'model': 'ARIMA(5,1,0)'
            })
        except Exception as e:
            return Response({"detail": f"An error occurred during prediction: {e}"}, status=500)

    @action(detail=True, methods=['get'])
    def predict_lstm(self, request, ticker=None):
        security = self.get_object()
        model_path = MODEL_DIR / f'{security.ticker}_lstm_model.h5'
        scaler_path = MODEL_DIR / f'{security.ticker}_lstm_scaler.joblib'
        if not model_path.exists() or not scaler_path.exists():
            return Response({"detail": "LSTM model or scaler not found."}, status=404)
        try:
            model = load_model(model_path)
            scaler = joblib.load(scaler_path)
            df = prepare_lstm_data(ticker)
            if df is None or len(df) < 60:
                return Response({"detail": "Not enough recent data to make a prediction."}, status=400)
            recent_data = df.tail(60)
            scaled_recent_data = scaler.transform(recent_data)
            X_pred = np.reshape(scaled_recent_data, (1, 60, scaled_recent_data.shape[1]))
            predicted_scaled_price = model.predict(X_pred)
            dummy_array = np.zeros((1, len(df.columns)))
            target_col_index = df.columns.get_loc('close')
            dummy_array[0, target_col_index] = predicted_scaled_price[0, 0]
            predicted_price = scaler.inverse_transform(dummy_array)[0, target_col_index]
            last_close = df['close'].iloc[-1]
            trend = "Up" if predicted_price > last_close else "Down" if predicted_price < last_close else "Neutral"
            return Response({
                'ticker': security.ticker,
                'last_close': float(last_close),
                'predicted_value': float(predicted_price),
                'trend': trend,
                'model': 'LSTM'
            })
        except Exception as e:
            return Response({"detail": f"An error occurred during LSTM prediction: {e}"}, status=500)

class SecurityPriceIntradayListView(generics.ListAPIView):
    serializer_class = SecurityPriceIntradaySerializer
    def get_queryset(self):
        ticker = self.kwargs['ticker'].upper()
        seven_days_ago = timezone.now() - timedelta(days=7)
        return SecurityPriceIntraday.objects.filter(security__ticker=ticker, datetime__gte=seven_days_ago).order_by('datetime')

# --- Frontend Template Views ---

class SecurityListView(ListView):
    model = Security
    template_name = "securities/security_list.html"

class SecurityDetailView(TemplateView):
    template_name = "securities/security_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticker = self.kwargs.get('ticker').upper()
        security = Security.objects.get(ticker=ticker)
        context['security'] = security
        if self.request.user.is_authenticated:
            watchlist, created = Watchlist.objects.get_or_create(user=self.request.user)
            context['watchlist'] = watchlist
            context['is_in_watchlist'] = watchlist.securities.filter(id=security.id).exists()
        return context
