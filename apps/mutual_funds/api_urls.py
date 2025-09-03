# apps/mutual_funds/api_urls.py
from rest_framework.routers import DefaultRouter
from apps.mutual_funds.views import MutualFundSchemeViewSet

router = DefaultRouter()
router.register(r'mutual-funds', MutualFundSchemeViewSet, basename='mutualfundscheme')

urlpatterns = router.urls
