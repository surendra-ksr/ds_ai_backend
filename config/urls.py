# config/urls.py
from django.contrib import admin
from django.urls import path, include

# API routes are grouped under /api/
api_urlpatterns = [
    path('', include('apps.securities.api_urls')),
    path('', include('apps.mutual_funds.api_urls')),
    path('', include('apps.analysis.api_urls')),
]

# Frontend routes for user-facing web pages
frontend_urlpatterns = [
    path('', include('apps.securities.urls')),
    path('', include('apps.mutual_funds.urls')),
]

# Main URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
    path('', include(frontend_urlpatterns)),
]
