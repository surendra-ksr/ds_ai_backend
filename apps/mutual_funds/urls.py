from rest_framework.routers import DefaultRouter
from .views import MutualFundSchemeViewSet

router = DefaultRouter()
router.register(r'mutual-funds', MutualFundSchemeViewSet, basename='mutualfundscheme')

urlpatterns = router.urls
