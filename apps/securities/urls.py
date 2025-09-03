# apps/securities/urls.py
from django.urls import path
from apps.securities.views import SecurityDetailView, SecurityListView

# These are the URLs for the user-facing web pages
urlpatterns = [
    path('securities/<str:ticker>/', SecurityDetailView.as_view(), name='security-detail'),
    path('', SecurityListView.as_view(), name='security-list'), # Homepage
]
