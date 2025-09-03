from rest_framework import serializers
from .models import Security, SecurityPrice, NewsArticle, Exchange

class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = ['name', 'currency']

class SecurityPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityPrice
        fields = [
            'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume',
            'sma_20', 'sma_50', 'sma_200', 'rsi', 'macd', 'bollinger_upper', 'bollinger_lower'
        ]

class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = ['source', 'headline', 'summary', 'url', 'published_at', 'sentiment_score']

class SecurityDetailSerializer(serializers.ModelSerializer):
    exchange = ExchangeSerializer(read_only=True)
    prices = SecurityPriceSerializer(many=True, read_only=True)
    news_articles = NewsArticleSerializer(many=True, read_only=True)

    class Meta:
        model = Security
        fields = ['ticker', 'name', 'sector', 'industry', 'exchange', 'prices', 'news_articles']

class SecurityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Security
        fields = ['ticker', 'name', 'sector', 'industry']
