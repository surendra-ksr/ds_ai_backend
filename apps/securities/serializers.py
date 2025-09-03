from rest_framework import serializers
from .models import Security, SecurityPrice, NewsArticle, Exchange, SecurityPriceIntraday
from apps.core.models import Category

class CategorySerializer(serializers.StringRelatedField):
    pass

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

class SecurityPriceIntradaySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityPriceIntraday
        fields = ['datetime', 'open', 'high', 'low', 'close', 'volume']

class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = ['source', 'headline', 'summary', 'url', 'published_at', 'sentiment_score']

class SecurityDetailSerializer(serializers.ModelSerializer):
    exchange = ExchangeSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    prices = SecurityPriceSerializer(many=True, read_only=True)
    news_articles = NewsArticleSerializer(many=True, read_only=True)

    class Meta:
        model = Security
        fields = ['ticker', 'name', 'exchange', 'categories', 'prices', 'news_articles']

class SecurityListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Security
        fields = ['ticker', 'name', 'categories']
