from django.db import models
from django.contrib.auth.models import User
from apps.securities.models import Security
from apps.mutual_funds.models import MutualFundScheme
from apps.core.models import BaseModel

class Watchlist(BaseModel):
    """
    A model to represent a user's watchlist, containing a collection of
    securities and mutual funds.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='watchlist')
    securities = models.ManyToManyField(Security, blank=True)
    mutual_funds = models.ManyToManyField(MutualFundScheme, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Watchlist"
