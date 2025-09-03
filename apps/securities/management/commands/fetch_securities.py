from django.core.management.base import BaseCommand
from apps.securities.models import Security, Exchange

# A list of major NSE-listed companies to seed the database
# In a real-world scenario, this would come from an API or a more comprehensive source
MAJOR_STOCKS = {
    'RELIANCE': 'Reliance Industries',
    'TCS': 'Tata Consultancy Services',
    'HDFCBANK': 'HDFC Bank',
    'INFY': 'Infosys',
    'HINDUNILVR': 'Hindustan Unilever',
    'ICICIBANK': 'ICICI Bank',
    'BHARTIARTL': 'Bharti Airtel',
    'SBIN': 'State Bank of India',
    'BAJFINANCE': 'Bajaj Finance',
    'KOTAKBANK': 'Kotak Mahindra Bank',
}

class Command(BaseCommand):
    """
    Seeds the database with a list of major securities from the NSE.
    """
    help = 'Seeds the database with major NSE securities.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding major securities...")

        # Get or create the NSE exchange
        nse_exchange, created = Exchange.objects.get_or_create(name='NSE', defaults={'currency': 'INR'})
        if created:
            self.stdout.write(self.style.SUCCESS('Created NSE exchange.'))

        for ticker, name in MAJOR_STOCKS.items():
            security, created = Security.objects.get_or_create(
                ticker=ticker,
                exchange=nse_exchange,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Added security: {name} ({ticker})'))
            else:
                self.stdout.write(self.style.WARNING(f'Security {name} ({ticker}) already exists.'))

        self.stdout.write(self.style.SUCCESS("Security seeding complete."))
