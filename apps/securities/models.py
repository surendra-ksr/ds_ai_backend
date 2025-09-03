from django.db import models
from apps.core.models import BaseModel, Category

class Exchange(BaseModel):
    name = models.CharField(max_length=50, unique=True, help_text="e.g., 'NSE', 'BSE'")
    currency = models.CharField(max_length=10, help_text="e.g., 'INR'")

    def __str__(self):
        return self.name

class Security(BaseModel):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='securities')
    ticker = models.CharField(max_length=20, help_text="e.g., 'RELIANCE'")
    name = models.CharField(max_length=255, help_text="e.g., 'Reliance Industries'")
    categories = models.ManyToManyField(Category, related_name='securities', blank=True)

    class Meta:
        unique_together = ('exchange', 'ticker')
        verbose_name_plural = "Securities"

    def __str__(self):
        return f"{self.name} ({self.ticker})"

class SecurityPrice(BaseModel):
    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField()
    open = models.DecimalField(max_digits=12, decimal_places=4)
    high = models.DecimalField(max_digits=12, decimal_places=4)
    low = models.DecimalField(max_digits=12, decimal_places=4)
    close = models.DecimalField(max_digits=12, decimal_places=4)
    adj_close = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField()

    # Technical Indicators
    sma_20 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    sma_50 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    sma_200 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    rsi = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    macd = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    bollinger_upper = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    bollinger_lower = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = ('security', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.security.ticker} on {self.date}"

class CorporateAction(BaseModel):
    ACTION_TYPES = [
        ('DIVIDEND', 'Dividend'),
        ('SPLIT', 'Split'),
        ('BONUS', 'Bonus'),
    ]
    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name='corporate_actions')
    ex_date = models.DateField()
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    details = models.JSONField(help_text="e.g., {'ratio': '1:2'} or {'dividend_per_share': 5.0}")

    class Meta:
        ordering = ['-ex_date']

    def __str__(self):
        return f"{self.security.ticker} - {self.action_type} on {self.ex_date}"

class NewsArticle(BaseModel):
    security = models.ForeignKey(Security, on_delete=models.SET_NULL, null=True, blank=True, related_name='news_articles')
    source = models.CharField(max_length=100)
    url = models.URLField(max_length=500, unique=True)
    headline = models.CharField(max_length=255)
    summary = models.TextField()
    published_at = models.DateTimeField()
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.headline
