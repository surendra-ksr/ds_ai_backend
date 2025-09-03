# apps/securities/api_urls.py
from rest_framework.routers import DefaultRouter
from apps.securities.views import SecurityViewSet

router = DefaultRouter()
router.register(r'securities', SecurityViewSet, basename='security')

urlpatterns = router.urls
