# E:/Repos/ds_ai_backend/config/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Include URLs from our apps
    # The API endpoints will be under /api/
    # The frontend pages will be under /
    path('api/', include('apps.analysis.urls')),
    path('', include('apps.securities.urls')),  # Contains both API and frontend URLs
    path('api/', include('apps.mutual_funds.urls')),
]
