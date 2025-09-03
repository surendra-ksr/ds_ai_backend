from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
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

class Portfolio(BaseModel):
    """Represents a user's investment portfolio.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    name = models.CharField(max_length=100, default="My Portfolio")

    def __str__(self):
        return f"{self.user.username}'s Portfolio"

class Transaction(BaseModel):
    """Represents a single transaction (buy/sell) within a portfolio.
    """
    TRANSACTION_TYPES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    
    # Generic relation to either a Security or a MutualFundScheme
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    price = models.DecimalField(max_digits=15, decimal_places=4, help_text="Price per unit")
    transaction_date = models.DateField()

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} of {self.content_object} on {self.transaction_date}"
