from django.db import models
from core.models import BaseModel, Category

class MutualFundHouse(BaseModel):
    name = models.CharField(max_length=255, unique=True, help_text="e.g., 'HDFC Mutual Fund'")

    def __str__(self):
        return self.name

class MutualFundScheme(BaseModel):
    fund_house = models.ForeignKey(MutualFundHouse, on_delete=models.CASCADE, related_name='schemes')
    scheme_code = models.IntegerField(unique=True, help_text="AMFI's unique scheme code")
    name = models.CharField(max_length=255)
    isin = models.CharField(max_length=20, unique=True, help_text="ISIN for the scheme")
    categories = models.ManyToManyField(Category, related_name='schemes', blank=True)

    def __str__(self):
        return self.name

class MutualFundNAV(BaseModel):
    scheme = models.ForeignKey(MutualFundScheme, on_delete=models.CASCADE, related_name='navs')
    date = models.DateField()
    nav = models.DecimalField(max_digits=12, decimal_places=4, help_text="Net Asset Value")

    class Meta:
        unique_together = ('scheme', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.scheme.name} - {self.nav} on {self.date}"
