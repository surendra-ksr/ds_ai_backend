from django.views.generic import ListView, TemplateView
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MutualFundScheme, MutualFundHouse
from apps.users.models import Watchlist
from .serializers import (
    MutualFundSchemeListSerializer,
    MutualFundSchemeDetailSerializer,
    MutualFundNAVSerializer
)
from collections import defaultdict

# --- API Views ---

class MutualFundSchemeViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    """
    A ViewSet for listing and retrieving Mutual Fund Schemes.
    Includes a custom action to retrieve historical NAV data.
    """
    queryset = MutualFundScheme.objects.select_related('fund_house').prefetch_related('categories')
    lookup_field = 'scheme_code'

    def get_serializer_class(self):
        if self.action == 'list':
            return MutualFundSchemeListSerializer
        if self.action == 'history':
            return MutualFundNAVSerializer
        return MutualFundSchemeDetailSerializer

    @action(detail=True, methods=['get'])
    def history(self, request, scheme_code=None):
        scheme = self.get_object()
        navs = scheme.navs.all().order_by('date')
        page = self.paginate_queryset(navs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(navs, many=True)
        return Response(serializer.data)

# --- Frontend Template Views ---

class MutualFundSchemeListView(ListView):
    model = MutualFundScheme
    template_name = "mutual_funds/mutual_fund_list.html"
    context_object_name = 'schemes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund_houses = defaultdict(list)
        queryset = self.get_queryset().select_related('fund_house').order_by('name')
        for scheme in queryset:
            fund_houses[scheme.fund_house.name].append(scheme)
        context['fund_houses'] = dict(sorted(fund_houses.items()))
        return context

class MutualFundSchemeDetailView(TemplateView):
    template_name = "mutual_funds/mutual_fund_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scheme_code = self.kwargs.get('scheme_code')
        scheme = MutualFundScheme.objects.get(scheme_code=scheme_code)
        context['scheme'] = scheme
        if self.request.user.is_authenticated:
            watchlist, created = Watchlist.objects.get_or_create(user=self.request.user)
            context['watchlist'] = watchlist
            context['is_in_watchlist'] = watchlist.mutual_funds.filter(id=scheme.id).exists()
        return context
