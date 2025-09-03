# apps/mutual_funds/urls.py
from django.urls import path
from apps.mutual_funds.views import MutualFundSchemeListView, MutualFundSchemeDetailView

# These are the URLs for the user-facing web pages
urlpatterns = [
    path('mutual-funds/', MutualFundSchemeListView.as_view(), name='mutual-fund-list'),
    path('mutual-funds/<int:scheme_code>/', MutualFundSchemeDetailView.as_view(), name='mutual-fund-detail'),
]
