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
    """
    queryset = Security.objects.all()
    lookup_field = 'ticker'

    def get_serializer_class(self):
        if self.action == 'list':
            return SecurityListSerializer
        return SecurityDetailSerializer

# --- Frontend Template Views ---

class SecurityDetailView(TemplateView):
    """
    Renders the main detail page for a single security.
    """
    template_name = "securities/security_detail.html"
