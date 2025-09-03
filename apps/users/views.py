from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Case, When, DecimalField

from .forms import RegistrationForm, TransactionForm
from .models import Watchlist, Security, MutualFundScheme, Portfolio, Transaction

# --- Template Views ---

class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        Watchlist.objects.create(user=user)
        Portfolio.objects.create(user=user) # Create a portfolio upon registration
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

@method_decorator(login_required, name='dispatch')
class WatchlistView(TemplateView):
    template_name = 'users/watchlist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        watchlist, created = Watchlist.objects.get_or_create(user=self.request.user)
        context['securities'] = watchlist.securities.all()
        context['mutual_funds'] = watchlist.mutual_funds.all()
        context['watchlist'] = watchlist
        return context

@method_decorator(login_required, name='dispatch')
class PortfolioView(TemplateView):
    template_name = 'users/portfolio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        portfolio, created = Portfolio.objects.get_or_create(user=self.request.user)
        transactions = portfolio.transactions.all().select_related('content_type')

        # Aggregate holdings
        holdings = {}
        for t in transactions:
            asset = t.content_object
            if asset not in holdings:
                holdings[asset] = {'quantity': 0, 'total_cost': 0}
            if t.transaction_type == 'BUY':
                holdings[asset]['quantity'] += t.quantity
                holdings[asset]['total_cost'] += t.quantity * t.price
            else: # SELL
                holdings[asset]['quantity'] -= t.quantity
        
        # Remove assets with zero quantity
        holdings = {asset: data for asset, data in holdings.items() if data['quantity'] > 0}

        context['holdings'] = holdings
        context['transaction_form'] = TransactionForm()
        return context

# --- API Views ---

class WatchlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        item_type = request.data.get('type')
        item_id = request.data.get('id')
        watchlist = request.user.watchlist
        try:
            if item_type == 'security': watchlist.securities.add(Security.objects.get(id=item_id))
            elif item_type == 'mutual_fund': watchlist.mutual_funds.add(MutualFundScheme.objects.get(id=item_id))
            else: return Response({'error': 'Invalid item type.'}, status=status.HTTP_400_BAD_REQUEST)
        except (Security.DoesNotExist, MutualFundScheme.DoesNotExist):
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'status': 'success', 'action': 'added'}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        item_type = request.data.get('type')
        item_id = request.data.get('id')
        watchlist = request.user.watchlist
        try:
            if item_type == 'security': watchlist.securities.remove(Security.objects.get(id=item_id))
            elif item_type == 'mutual_fund': watchlist.mutual_funds.remove(MutualFundScheme.objects.get(id=item_id))
        except (Security.DoesNotExist, MutualFundScheme.DoesNotExist): pass
        return Response({'status': 'success', 'action': 'removed'}, status=status.HTTP_200_OK)

class TransactionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        form = TransactionForm(request.data)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.portfolio = request.user.portfolio
            transaction.save()
            return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        transaction_id = request.data.get('id')
        try:
            transaction = Transaction.objects.get(id=transaction_id, portfolio=request.user.portfolio)
            transaction.delete()
            return Response({'status': 'success'}, status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found.'}, status=status.HTTP_404_NOT_FOUND)
