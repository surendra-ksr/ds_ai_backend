import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.securities.models import MarketIndex, MarketIndexPrice

# Placeholder data for major Indian indices
INDEX_DATA = {
    'NIFTY 50': {
        'ticker': 'NIFTY_50',
        'prices': [
            {'date': '2023-10-26', 'open': 19000, 'high': 19100, 'low': 18900, 'close': 19050},
            {'date': '2023-10-27', 'open': 19050, 'high': 19250, 'low': 19000, 'close': 19200},
        ]
    },
    'SENSEX': {
        'ticker': 'SENSEX',
        'prices': [
            {'date': '2023-10-26', 'open': 63000, 'high': 63500, 'low': 62800, 'close': 63300},
            {'date': '2023-10-27', 'open': 63300, 'high': 64000, 'low': 63200, 'close': 63900},
        ]
    }
}

class Command(BaseCommand):
    """
    Populates the database with major market indices and their (placeholder) price data.
    """
    help = 'Fetches and stores market index data.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding market index data...")

        for name, data in INDEX_DATA.items():
            index, created = MarketIndex.objects.get_or_create(
                name=name,
                defaults={'ticker': data['ticker']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created index: {name}'))
            
            for price_data in data['prices']:
                MarketIndexPrice.objects.get_or_create(
                    index=index,
                    date=datetime.date.fromisoformat(price_data['date']),
                    defaults={
                        'open': Decimal(price_data['open']),
                        'high': Decimal(price_data['high']),
                        'low': Decimal(price_data['low']),
                        'close': Decimal(price_data['close']),
                    }
                )

        self.stdout.write(self.style.SUCCESS("Market index data seeding complete."))
