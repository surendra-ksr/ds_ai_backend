from rest_framework import viewsets, mixins
from .models import MutualFundScheme
from .serializers import MutualFundSchemeListSerializer, MutualFundSchemeDetailSerializer

class MutualFundSchemeViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    """
    A ViewSet for listing and retrieving Mutual Fund Schemes.
    """
    queryset = MutualFundScheme.objects.all()
    lookup_field = 'scheme_code'

    def get_serializer_class(self):
        if self.action == 'list':
            return MutualFundSchemeListSerializer
        return MutualFundSchemeDetailSerializer
