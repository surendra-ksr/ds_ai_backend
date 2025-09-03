from django.views.generic import TemplateView, ListView
from rest_framework import viewsets, mixins, generics
from .models import Security, SecurityPriceIntraday
from .serializers import SecurityListSerializer, SecurityDetailSerializer, SecurityPriceIntradaySerializer

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

class SecurityPriceIntradayListView(generics.ListAPIView):
    """
    An API view to list all intraday price points for a given security ticker.
    """
    serializer_class = SecurityPriceIntradaySerializer

    def get_queryset(self):
        ticker = self.kwargs['ticker'].upper()
        return SecurityPriceIntraday.objects.filter(security__ticker=ticker).order_by('datetime')

# --- Frontend Template Views ---

class SecurityListView(ListView):
    """
    Renders a homepage with a list of all securities.
    """
    model = Security
    template_name = "securities/security_list.html"

class SecurityDetailView(TemplateView):
    """
    Renders the main detail page for a single security.
    """
    template_name = "securities/security_detail.html"
