from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SecurityViewSet, SecurityDetailView, SecurityListView

# API Router
router = DefaultRouter()
router.register(r'securities', SecurityViewSet, basename='security')

# The API URLs are now determined automatically by the router.
# The frontend URLs are defined separately.
urlpatterns = [
    path('api/', include(router.urls)),
    path('securities/<str:ticker>/', SecurityDetailView.as_view(), name='security-detail'),
    path('', SecurityListView.as_view(), name='security-list'), # Homepage
]
