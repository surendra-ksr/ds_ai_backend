from django.urls import path
from .views import PredictionListView

urlpatterns = [
    path('analysis/<str:ticker>/predictions/', PredictionListView.as_view(), name='security-predictions'),
]
