import os
import requests
import spacy
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from apps.securities.models import Security, NewsArticle

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None

# --- API Configuration ---
NEWSAPI_URL = "https://newsapi.org/v2/everything"
NEWSAPI_KEY = os.environ.get("NEWS_API_KEY")

MARKETAUX_URL = "https://api.marketaux.com/v1/news/all"
MARKETAUX_KEY = os.environ.get("MARKETAUX_API_KEY")

class Command(BaseCommand):
    help = 'Fetches and analyzes news sentiment for one or all securities.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', type=str, help='Optional ticker symbol to fetch news for.')
        parser.add_argument('--all', action='store_true', help='Fetch news for all securities in the database.')

    def handle(self, *args, **options):
        if nlp is None:
            raise CommandError("spaCy model is not loaded. Please install it first.")

        if options['all']:
            securities = Security.objects.all()
            self.stdout.write(self.style.SUCCESS(f"Fetching news for all {securities.count()} securities..."))
            for security in tqdm(securities, desc="Fetching News"):
                self.fetch_for_security(security)
        elif options['ticker']:
            try:
                security = Security.objects.get(ticker=options['ticker'].split('.')[0])
                self.fetch_for_security(security)
            except Security.DoesNotExist:
                raise CommandError(f"Security {options['ticker']} not found.")
        else:
            raise CommandError("No ticker specified. Provide a ticker or use the --all flag.")

    def fetch_for_security(self, security):
        query = f'"{security.name}" OR {security.ticker}'
        articles = self.fetch_from_newsapi(query)

        # Fallback to Marketaux if NewsAPI fails or returns no articles
        if not articles and MARKETAUX_KEY:
            articles = self.fetch_from_marketaux(security.ticker)
        
        if not articles:
            return

        for article_data in articles:
            # Use the URL as a unique identifier to avoid duplicates
            _, created = NewsArticle.objects.get_or_create(
                url=article_data['url'],
                defaults={
                    'security': security,
                    'source': article_data['source'],
                    'headline': article_data['headline'],
                    'summary': article_data['summary'],
                    'published_at': article_data['published_at'],
                    'sentiment_score': self.analyze_sentiment(article_data['headline'] + " " + article_data['summary']),
                }
            )

    def fetch_from_newsapi(self, query):
        if not NEWSAPI_KEY:
            return []
        params = {'q': query, 'apiKey': NEWSAPI_KEY, 'language': 'en', 'sortBy': 'publishedAt', 'pageSize': 10}
        try:
            response = requests.get(NEWSAPI_URL, params=params)
            response.raise_for_status()
            return [
                {
                    'url': a['url'], 'source': a['source']['name'], 'headline': a['title'],
                    'summary': a.get('description', '') or '', 'published_at': a['publishedAt']
                }
                for a in response.json().get('articles', [])
            ]
        except requests.exceptions.RequestException:
            return []

    def fetch_from_marketaux(self, ticker):
        params = {'symbols': ticker, 'api_token': MARKETAUX_KEY, 'language': 'en'}
        try:
            response = requests.get(MARKETAUX_URL, params=params)
            response.raise_for_status()
            return [
                {
                    'url': a['url'], 'source': a['source'], 'headline': a['title'],
                    'summary': a.get('description', '') or '', 'published_at': a['published_at']
                }
                for a in response.json().get('data', [])
            ]
        except requests.exceptions.RequestException:
            return []

    def analyze_sentiment(self, text: str) -> float:
        doc = nlp(text.lower())
        pos_words = ['good', 'great', 'excellent', 'positive', 'up', 'strong', 'buy', 'bullish', 'profit', 'gain']
        neg_words = ['bad', 'poor', 'terrible', 'negative', 'down', 'weak', 'sell', 'bearish', 'loss']
        score = sum(1 for token in doc if token.lemma_ in pos_words) - sum(1 for token in doc if token.lemma_ in neg_words)
        return max(-1.0, min(1.0, score / len(doc))) if len(doc) > 0 else 0.0
