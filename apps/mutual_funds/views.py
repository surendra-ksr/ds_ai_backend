from django.views.generic import ListView, TemplateView
from rest_framework import viewsets, mixins
from .models import MutualFundScheme, MutualFundHouse
from .serializers import MutualFundSchemeListSerializer, MutualFundSchemeDetailSerializer
from collections import defaultdict

# --- API Views ---

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

# --- Frontend Template Views ---

class MutualFundSchemeListView(ListView):
    """
    Renders a page with a list of all mutual fund schemes, grouped by fund house.
    """
    model = MutualFundScheme
    template_name = "mutual_funds/mutual_fund_list.html"
    context_object_name = 'schemes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund_houses = defaultdict(list)
        for scheme in self.get_queryset().select_related('fund_house'):
            fund_houses[scheme.fund_house.name].append(scheme)
        context['fund_houses'] = dict(sorted(fund_houses.items()))
        return context

class MutualFundSchemeDetailView(TemplateView):
    """
    Renders the main detail page for a single mutual fund scheme.
    """
    template_name = "mutual_funds/mutual_fund_detail.html"
