from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import RegisterView, CustomLoginView, WatchlistView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='security-list'), name='logout'), # Redirect to homepage on logout
    path('watchlist/', WatchlistView.as_view(), name='watchlist'),
]
