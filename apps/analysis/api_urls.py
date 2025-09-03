# apps/analysis/api_urls.py
from django.urls import path
from apps.analysis.views import PredictionListView

urlpatterns = [
    path('analysis/<str:ticker>/predictions/', PredictionListView.as_view(), name='security-predictions'),
]
