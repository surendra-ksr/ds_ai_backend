import os
import requests
import spacy
from django.core.management.base import BaseCommand, CommandError
from apps.securities.models import Security, NewsArticle
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from collections import Counter
from heapq import nlargest

# Load the spaCy model. 
# You may need to run: python -m spacy download en_core_web_sm
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None

# --- IMPORTANT --- 
# This is a placeholder for a real news API. 
# You should sign up for a service like NewsAPI.org, Newsdata.io, or Marketaux
# and get a real API key. Store it in an environment variable.
NEWS_API_URL = "https://newsapi.org/v2/everything"
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "YOUR_API_KEY_HERE")

class Command(BaseCommand):
    help = 'Fetches and analyzes news sentiment for a given security.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', type=str, help='The ticker symbol of the security to fetch news for.')

    def handle(self, *args, **options):
        if nlp is None:
            raise CommandError("spaCy model is not loaded. Please install it first.")

        if NEWS_API_KEY == "YOUR_API_KEY_HERE":
            self.stdout.write(self.style.WARNING("NEWS_API_KEY is not set. Using placeholder data."))
            # In a real scenario, you would raise a CommandError here.

        ticker_symbol = options['ticker']
        self.stdout.write(f"Fetching news for {ticker_symbol}...")

        try:
            security = Security.objects.get(ticker=ticker_symbol.split('.')[0])
        except Security.DoesNotExist:
            raise CommandError(f"Security {ticker_symbol} not found in the database.")

        # --- API Call ---
        params = {
            'q': security.name, # Search by the full name of the company for better results
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 20 # Limit to recent articles
        }
        try:
            response = requests.get(NEWS_API_URL, params=params)
            response.raise_for_status()
            articles = response.json().get('articles', [])
        except requests.exceptions.RequestException as e:
            raise CommandError(f"Failed to fetch news from API: {e}")

        if not articles:
            self.stdout.write(self.style.SUCCESS("No new articles found."))
            return

        saved_count = 0
        for article in articles:
            # Use the URL as a unique identifier to avoid duplicates
            _, created = NewsArticle.objects.get_or_create(
                url=article['url'],
                defaults={
                    'security': security,
                    'source': article['source']['name'],
                    'headline': article['title'],
                    'summary': article.get('description', ''),
                    'published_at': article['publishedAt'],
                    'sentiment_score': self.analyze_sentiment(article['title'] + " " + article.get('description', '')),
                }
            )
            if created:
                saved_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully saved {saved_count} new articles."))

    def analyze_sentiment(self, text: str) -> float:
        """Analyzes sentiment of a text, returning a score from -1.0 to 1.0."""
        # A simple sentiment analysis using spaCy's textcat (if trained) or a basic keyword approach.
        # For a more robust solution, consider libraries like TextBlob or VADER.
        # This is a simplified example.
        doc = nlp(text.lower())
        
        # Basic polarity check (this is a naive implementation)
        pos_words = ['good', 'great', 'excellent', 'positive', 'up', 'strong', 'buy', 'bullish', 'profit', 'gain']
        neg_words = ['bad', 'poor', 'terrible', 'negative', 'down', 'weak', 'sell', 'bearish', 'loss']
        
        score = 0
        for token in doc:
            if token.lemma_ in pos_words:
                score += 1
            elif token.lemma_ in neg_words:
                score -= 1
        
        # Normalize score to be between -1 and 1
        if len(doc) > 0:
            return max(-1.0, min(1.0, score / len(doc)))
        return 0.0
