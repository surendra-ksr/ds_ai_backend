from django.db import models
from apps.core.models import BaseModel, Category

class MutualFundHouse(BaseModel):
    name = models.CharField(max_length=255, unique=True, help_text="e.g., 'HDFC Mutual Fund'")

    def __str__(self):
        return self.name

class MutualFundScheme(BaseModel):
    fund_house = models.ForeignKey(MutualFundHouse, on_delete=models.CASCADE, related_name='schemes')
    scheme_code = models.IntegerField(help_text="AMFI's scheme code")
    name = models.CharField(max_length=255)
    isin = models.CharField(max_length=20, unique=True, help_text="ISIN for the scheme")
    categories = models.ManyToManyField(Category, related_name='schemes', blank=True)
    # New field for Assets Under Management
    aum = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, help_text="Assets Under Management in Crores")

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

class MutualFundPerformance(BaseModel):
    scheme = models.OneToOneField(MutualFundScheme, on_delete=models.CASCADE, related_name='performance')
    return_1y = models.FloatField(null=True, blank=True, help_text="1-Year Annualized Return")
    return_3y = models.FloatField(null=True, blank=True, help_text="3-Year Annualized Return")
    return_5y = models.FloatField(null=True, blank=True, help_text="5-Year Annualized Return")
    ytd_return = models.FloatField(null=True, blank=True, help_text="Year-to-Date Return")

    def __str__(self):
        return f"Performance for {self.scheme.name}"
