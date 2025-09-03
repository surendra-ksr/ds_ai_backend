# config/urls.py
from django.contrib import admin
from django.urls import path, include

# API routes are grouped under /api/
api_urlpatterns = [
    path('', include('apps.securities.api_urls')),
    path('', include('apps.mutual_funds.api_urls')),
    path('', include('apps.analysis.api_urls')),
    path('', include('apps.users.api_urls')), # Add user watchlist API
]

# Frontend routes for user-facing web pages
frontend_urlpatterns = [
    path('', include('apps.securities.urls')),
    path('', include('apps.mutual_funds.urls')),
    path('accounts/', include('apps.users.urls')), # Add user auth routes
]

# Main URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
    path('', include(frontend_urlpatterns)),
]
