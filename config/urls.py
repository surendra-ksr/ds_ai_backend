# E:/Repos/ds_ai_backend/config/urls.py

from django.contrib import admin
from django.urls import path, include

# API routes are handled by their respective apps
api_urlpatterns = [
    path('', include('securities.urls')),
    path('', include('mutual_funds.urls')),
    path('', include('analysis.urls')),
]

# Main URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),

    # The frontend view for a single security is also in the securities app
    path('securities/<str:ticker>/', include('securities.urls')),
]
