from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MutualFundSchemeViewSet, MutualFundSchemeListView, MutualFundSchemeDetailView

# API Router
router = DefaultRouter()
router.register(r'mutual-funds', MutualFundSchemeViewSet, basename='mutualfundscheme')

# The API URLs are now determined automatically by the router.
# The frontend URLs are defined separately.
urlpatterns = [
    path('api/', include(router.urls)),
    path('mutual-funds/', MutualFundSchemeListView.as_view(), name='mutual-fund-list'),
    path('mutual-funds/<int:scheme_code>/', MutualFundSchemeDetailView.as_view(), name='mutual-fund-detail'),
]
