# apps/securities/urls.py
from django.urls import path
from apps.securities.views import SecurityDetailView, MarketDashboardView, StockScreenerView

# These are the URLs for the user-facing web pages
urlpatterns = [
    path('securities/<str:ticker>/', SecurityDetailView.as_view(), name='security-detail'),
    path('screener/', StockScreenerView.as_view(), name='stock-screener'),
    path('', MarketDashboardView.as_view(), name='security-list'), # Homepage
]
