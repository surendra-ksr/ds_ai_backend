from django.views.generic import TemplateView
from rest_framework import viewsets, mixins
from .models import Security
from .serializers import SecurityListSerializer, SecurityDetailSerializer

# --- API Views ---

class SecurityViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    """
    A ViewSet for listing and retrieving securities.
    
    - `list`: Returns a list of all securities with basic information.
    - `retrieve`: Returns detailed information for a single security, including prices and news.
    """
    queryset = Security.objects.all()
    lookup_field = 'ticker' # Use the ticker symbol in the URL (e.g., /api/securities/RELIANCE/)

    def get_serializer_class(self):
        """Return different serializers for list and retrieve actions."""
        if self.action == 'list':
            return SecurityListSerializer
        return SecurityDetailSerializer

# --- Frontend Template Views ---

class SecurityDetailView(TemplateView):
    """
    Renders the main detail page for a single security.
    The data is fetched client-side via the API.
    """
    template_name = "securities/security_detail.html"
