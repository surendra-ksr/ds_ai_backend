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

from .forms import RegistrationForm
from .models import Watchlist, Security, MutualFundScheme

# --- Template Views ---

class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        Watchlist.objects.create(user=user)
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
        # Pass the full watchlist object to check for items in the template
        context['watchlist'] = watchlist
        return context

# --- API Views ---

class WatchlistAPIView(APIView):
    """
    API endpoint for managing a user's watchlist.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Add an item to the watchlist."""
        item_type = request.data.get('type')
        item_id = request.data.get('id')

        if not item_type or not item_id:
            return Response({'error': 'Type and ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

        watchlist = request.user.watchlist

        try:
            if item_type == 'security':
                security = Security.objects.get(id=item_id)
                watchlist.securities.add(security)
            elif item_type == 'mutual_fund':
                mf = MutualFundScheme.objects.get(id=item_id)
                watchlist.mutual_funds.add(mf)
            else:
                return Response({'error': 'Invalid item type.'}, status=status.HTTP_400_BAD_REQUEST)
        except (Security.DoesNotExist, MutualFundScheme.DoesNotExist):
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': 'success', 'action': 'added'}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Remove an item from the watchlist."""
        item_type = request.data.get('type')
        item_id = request.data.get('id')

        if not item_type or not item_id:
            return Response({'error': 'Type and ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

        watchlist = request.user.watchlist

        try:
            if item_type == 'security':
                security = Security.objects.get(id=item_id)
                watchlist.securities.remove(security)
            elif item_type == 'mutual_fund':
                mf = MutualFundScheme.objects.get(id=item_id)
                watchlist.mutual_funds.remove(mf)
            else:
                return Response({'error': 'Invalid item type.'}, status=status.HTTP_400_BAD_REQUEST)
        except (Security.DoesNotExist, MutualFundScheme.DoesNotExist):
            # It's okay if the item doesn't exist, the goal is to ensure it's not on the list
            pass

        return Response({'status': 'success', 'action': 'removed'}, status=status.HTTP_200_OK)
