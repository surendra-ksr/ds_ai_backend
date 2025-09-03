from django.utils import timezone
from datetime import timedelta
from django.views.generic import TemplateView, ListView
from django.conf import settings
from django.db.models import F, Window, Subquery, OuterRef
from django.db.models.functions import Lag
from rest_framework import viewsets, mixins, generics
from rest_framework.decorators import action
from rest_framework.response import Response
import pandas as pd
import joblib
from pathlib import Path
import numpy as np
from tensorflow.keras.models import load_model

from apps.analysis.data_processing import prepare_lstm_data
from .models import Security, SecurityPrice, SecurityPriceIntraday, NewsArticle, MarketIndex, MarketIndexPrice
from apps.users.models import Watchlist
from .forms import ScreenerForm
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
    queryset = Security.objects.all()
    lookup_field = 'ticker'

    def get_serializer_class(self):
        if self.action == 'list': return SecurityListSerializer
        if self.action == 'news': return NewsArticleSerializer
        return SecurityDetailSerializer

    @action(detail=True, methods=['get'])
    def analysis(self, request, ticker=None):
        # Import pandas_ta locally. This is critical to avoid startup errors on Windows
        # where this library can cause a ModuleNotFoundError for 'posix'.
        import pandas_ta as ta

        security = self.get_object()
        prices = SecurityPrice.objects.filter(security=security).order_by('date')
        if not prices.exists(): return Response({"detail": "No historical price data found."}, status=404)
        df = pd.DataFrame.from_records(prices.values('date', 'open', 'high', 'low', 'close', 'volume'))
        df.set_index('date', inplace=True)
        df.ta.sma(length=20, append=True); df.ta.sma(length=50, append=True); df.ta.rsi(length=14, append=True); df.ta.macd(append=True)
        df.reset_index(inplace=True)
        return Response(df.where(pd.notnull(df), None).to_dict(orient='records'))

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
        if not model_path.exists(): return Response({"detail": "No trained model found."}, status=404)
        try:
            model_fit = joblib.load(str(model_path))
            forecast = model_fit.get_forecast(steps=1)
            predicted_value = forecast.predicted_mean.iloc[0]
            last_price = SecurityPrice.objects.filter(security=security).latest('date').close
            trend = "Up" if predicted_value > last_price else "Down" if predicted_value < last_price else "Neutral"
            return Response({'predicted_value': float(predicted_value), 'trend': trend, 'model': 'ARIMA'})
        except Exception as e: return Response({"detail": str(e)}, status=500)

    @action(detail=True, methods=['get'])
    def predict_lstm(self, request, ticker=None):
        security = self.get_object()
        model_path = MODEL_DIR / f'{security.ticker}_lstm_model.h5'
        scaler_path = MODEL_DIR / f'{security.ticker}_lstm_scaler.joblib'
        if not model_path.exists() or not scaler_path.exists(): return Response({"detail": "LSTM model not found."}, status=404)
        try:
            model = load_model(str(model_path)); scaler = joblib.load(str(scaler_path))
            df = prepare_lstm_data(ticker)
            if df is None or len(df) < 60: return Response({"detail": "Not enough data."}, status=400)
            recent_data = df.tail(60); scaled_recent_data = scaler.transform(recent_data)
            X_pred = np.reshape(scaled_recent_data, (1, 60, scaled_recent_data.shape[1]))
            predicted_scaled_price = model.predict(X_pred)
            dummy_array = np.zeros((1, len(df.columns))); target_col_index = df.columns.get_loc('close')
            dummy_array[0, target_col_index] = predicted_scaled_price[0, 0]
            predicted_price = scaler.inverse_transform(dummy_array)[0, target_col_index]
            last_close = df['close'].iloc[-1]
            trend = "Up" if predicted_price > last_close else "Down" if predicted_price < last_close else "Neutral"
            return Response({'predicted_value': float(predicted_price), 'trend': trend, 'model': 'LSTM'})
        except Exception as e: return Response({"detail": str(e)}, status=500)

class SecurityPriceIntradayListView(generics.ListAPIView):
    serializer_class = SecurityPriceIntradaySerializer
    def get_queryset(self):
        ticker = self.kwargs['ticker'].upper()
        seven_days_ago = timezone.now() - timedelta(days=7)
        return SecurityPriceIntraday.objects.filter(security__ticker=ticker, datetime__gte=seven_days_ago).order_by('datetime')

# --- Frontend Template Views ---

class MarketDashboardView(TemplateView):
    template_name = "securities/market_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_prices = SecurityPrice.objects.filter(security=OuterRef('pk')).order_by('-date')
        securities = Security.objects.annotate(
            latest_close=Subquery(latest_prices.values('close')[:1]),
            prev_close=Subquery(latest_prices.values('close')[1:2]),
            latest_volume=Subquery(latest_prices.values('volume')[:1])
        ).filter(latest_close__isnull=False, prev_close__isnull=False)
        securities = securities.annotate(
            price_change=F('latest_close') - F('prev_close'),
            percentage_change=(F('latest_close') - F('prev_close')) * 100.0 / F('prev_close')
        )
        context['top_gainers'] = securities.order_by('-percentage_change')[:5]
        context['top_losers'] = securities.order_by('percentage_change')[:5]
        context['most_active'] = securities.order_by('-latest_volume')[:5]
        context['market_indices'] = MarketIndex.objects.all()
        return context

class StockScreenerView(ListView):
    model = Security
    template_name = 'securities/stock_screener.html'
    context_object_name = 'securities'

    def get_queryset(self):
        queryset = super().get_queryset()
        form = ScreenerForm(self.request.GET)

        if form.is_valid():
            if form.cleaned_data.get('min_market_cap'):
                queryset = queryset.filter(market_cap__gte=form.cleaned_data['min_market_cap'] * 1_00_00_000)
            if form.cleaned_data.get('max_pe_ratio'):
                queryset = queryset.filter(pe_ratio__lte=form.cleaned_data['max_pe_ratio'])
            if form.cleaned_data.get('min_dividend_yield'):
                queryset = queryset.filter(dividend_yield__gte=form.cleaned_data['min_dividend_yield'])

            sort_by = form.cleaned_data.get('sort_by')
            if sort_by:
                if sort_by == 'market_cap_desc': queryset = queryset.order_by(F('market_cap').desc(nulls_last=True))
                elif sort_by == 'market_cap_asc': queryset = queryset.order_by(F('market_cap').asc(nulls_last=True))
                elif sort_by == 'pe_ratio_asc': queryset = queryset.order_by(F('pe_ratio').asc(nulls_last=True))
                elif sort_by == 'dividend_yield_desc': queryset = queryset.order_by(F('dividend_yield').desc(nulls_last=True))
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ScreenerForm(self.request.GET)
        return context

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
