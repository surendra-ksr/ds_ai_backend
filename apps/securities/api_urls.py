# apps/securities/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.securities.views import SecurityViewSet, SecurityPriceIntradayListView

router = DefaultRouter()
router.register(r'securities', SecurityViewSet, basename='security')

urlpatterns = [
    path('', include(router.urls)),
    path('securities/<str:ticker>/intraday/', SecurityPriceIntradayListView.as_view(), name='security-intraday-prices'),
]
