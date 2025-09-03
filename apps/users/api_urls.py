from django.urls import path
from .views import WatchlistAPIView

urlpatterns = [
    path('watchlist/', WatchlistAPIView.as_view(), name='api-watchlist'),
]
