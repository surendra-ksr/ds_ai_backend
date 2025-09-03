from rest_framework import viewsets, mixins
from .models import MutualFundScheme
from .serializers import MutualFundSchemeListSerializer, MutualFundSchemeDetailSerializer

class MutualFundSchemeViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    """
    A ViewSet for listing and retrieving Mutual Fund Schemes.

    - `list`: Returns a list of all schemes with basic information.
    - `retrieve`: Returns detailed information for a single scheme, including its NAV history.
    """
    queryset = MutualFundScheme.objects.all()
    serializer_class = MutualFundSchemeListSerializer
    lookup_field = 'scheme_code' # Use the unique scheme_code in the URL

    def get_serializer_class(self):
        if self.action == 'list':
            return MutualFundSchemeListSerializer
        return MutualFundSchemeDetailSerializer
