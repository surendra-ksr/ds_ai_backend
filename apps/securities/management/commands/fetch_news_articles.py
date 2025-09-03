import requests
import os
import spacy
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from apps.securities.models import Security, NewsArticle
from tqdm import tqdm

# Load the spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
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
        if not text: return 0.0
        return nlp(text).sentiment

    def handle(self, *args, **options):
        api_key = os.environ.get('NEWSDATA_API_KEY')
        if not api_key:
            self.stdout.write(self.style.WARNING(
                "NEWSDATA_API_KEY environment variable not set. Using mock data instead. " \
                "For real data, get a key from newsdata.io and set the environment variable."
            ))

        if options['all']:
            securities = list(Security.objects.all())
        elif options['tickers']:
            securities = list(Security.objects.filter(ticker__in=[t.upper() for t in options['tickers']]))
        else:
            raise CommandError("No securities specified. Use tickers or the --all flag.")
        
        if not securities:
            raise CommandError("No securities found for the given criteria.")

        self.stdout.write(f"Fetching news for {len(securities)} securities...")

        for security in tqdm(securities, desc="Fetching News"):
            try:
                if api_key:
                    url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={security.name}&language=en&country=in"
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    articles = data.get("results", [])
                else:
                    # Using mock data if no API key is provided
                    articles = [
                        {"source_id": "mock-source", "link": f"https://example.com/news/{security.ticker.lower()}-1", "title": f"{security.name} Announces Record Profits", "description": "Positive development.", "pubDate": "2023-10-27 10:00:00"},
                        {"source_id": "mock-source", "link": f"https://example.com/news/{security.ticker.lower()}-2", "title": f"Regulatory Concerns Loom Over {security.name}", "description": "Investors are worried.", "pubDate": "2023-10-26 15:30:00"}
                    ]

                if not articles:
                    continue

                articles_to_create = []
                for article in articles:
                    if NewsArticle.objects.filter(url=article['link']).exists():
                        continue

                    headline = article.get('title', '')
                    summary = article.get('description', '')
                    text_to_analyze = f"{headline}. {summary}"
                    sentiment_score = self.get_sentiment(text_to_analyze)
                    published_at = parse_datetime(article['pubDate'])

                    if published_at:
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

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Skipping {security.ticker} due to an error: {e}"))
                continue

        self.stdout.write(self.style.SUCCESS("\nNews fetching complete."))
