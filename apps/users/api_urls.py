from django.urls import path
from .views import WatchlistAPIView, TransactionAPIView

urlpatterns = [
    path('watchlist/', WatchlistAPIView.as_view(), name='api-watchlist'),
    path('transactions/', TransactionAPIView.as_view(), name='api-transactions'),
]
