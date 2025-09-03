import requests
import os
import spacy
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from apps.securities.models import Security, NewsArticle

# Load the spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # This will be raised if the model isn't downloaded. 
    # Advise the user to download it.
    raise CommandError("spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")

class Command(BaseCommand):
    """
    Fetches news articles for tracked securities from a news API, 
    analyzes their sentiment, and stores them in the database.
    """
    help = 'Fetches and analyzes news articles for specified securities.'

    def add_arguments(self, parser):
        parser.add_argument('tickers', nargs='*', type=str, help='A list of security tickers to fetch news for.')
        parser.add_argument('--all', action='store_true', help='Fetch news for all securities in the database.')

    def get_sentiment(self, text):
        """Analyzes the sentiment of a given text using spaCy.
        Returns a sentiment score between -1 (negative) and 1 (positive).
        """
        if not text:
            return 0.0
        doc = nlp(text)
        # VADER sentiment is often included with spaCy extensions, but polarity is a good basic measure.
        return doc.sentiment

    def handle(self, *args, **options):
        # --- Configuration ---
        # IMPORTANT: It is strongly recommended to use a more secure way to store API keys,
        # such as Django settings loaded from environment variables.
        api_key = os.environ.get('NEWSDATA_API_KEY')
        if not api_key:
            self.stdout.write(self.style.WARNING(
                "NEWSDATA_API_KEY environment variable not set. Using mock data instead. " \
                "For real data, get a key from newsdata.io and set the environment variable."
            ))

        securities = []
        if options['all']:
            securities = list(Security.objects.all())
        elif options['tickers']:
            securities = list(Security.objects.filter(ticker__in=[t.upper() for t in options['tickers']]))
        
        if not securities:
            raise CommandError("No securities specified or found. Use tickers or the --all flag.")

        self.stdout.write(f"Fetching news for {len(securities)} securities...")

        for security in securities:
            self.stdout.write(self.style.SUCCESS(f"Processing: {security.ticker}"))

            if api_key:
                # --- Live API Call ---
                url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={security.name}&language=en&country=in"
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    articles = data.get("results", [])
                except requests.exceptions.RequestException as e:
                    self.stderr.write(self.style.ERROR(f"API request failed for {security.ticker}: {e}"))
                    continue
            else:
                # --- Mock Data for Development ---
                articles = [
                    {
                        "source_id": "mock-source",
                        "link": f"https://example.com/news/{security.ticker.lower()}-1",
                        "title": f"{security.name} Announces Record Profits",
                        "description": "A very positive development for the company, with shares expected to rise.",
                        "pubDate": "2023-10-27 10:00:00",
                    },
                    {
                        "source_id": "mock-source",
                        "link": f"https://example.com/news/{security.ticker.lower()}-2",
                        "title": f"Regulatory Concerns Loom Over {security.name}",
                        "description": "Investors are worried about potential new regulations that could impact the sector.",
                        "pubDate": "2023-10-26 15:30:00",
                    }
                ]

            if not articles:
                self.stdout.write(self.style.WARNING(f"No articles found for {security.ticker}"))
                continue

            articles_to_create = []
            for article in articles:
                # Skip if we already have this article (based on URL)
                if NewsArticle.objects.filter(url=article['link']).exists():
                    continue

                headline = article.get('title', '')
                summary = article.get('description', '')
                text_to_analyze = f"{headline}. {summary}"
                sentiment_score = self.get_sentiment(text_to_analyze)

                # The date format from newsdata.io is 'YYYY-MM-DD HH:MM:SS'
                published_at = parse_datetime(article['pubDate'])

                articles_to_create.append(
                    NewsArticle(
                        security=security,
                        source=article.get('source_id', 'N/A'),
                        url=article['link'],
                        headline=headline,
                        summary=summary,
                        published_at=published_at,
                        sentiment_score=sentiment_score
                    )
                )
            
            if articles_to_create:
                NewsArticle.objects.bulk_create(articles_to_create, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(f"  -> Saved {len(articles_to_create)} new articles for {security.ticker}"))
            else:
                self.stdout.write(f"  -> No new articles to save for {security.ticker}")

        self.stdout.write(self.style.SUCCESS("\nNews fetching complete.")) 
