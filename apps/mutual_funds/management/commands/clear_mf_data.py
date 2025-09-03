from django.core.management.base import BaseCommand
from django.db import transaction
from apps.mutual_funds.models import MutualFundScheme, MutualFundNAV, MutualFundPerformance

class Command(BaseCommand):
    help = 'Deletes all data from the mutual fund tables to allow for a clean re-population.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Required to confirm the deletion of all mutual fund data.',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.ERROR("This is a destructive operation. You must use the --confirm flag to proceed."))
            return

        self.stdout.write(self.style.WARNING("Deleting all mutual fund related data..."))

        with transaction.atomic():
            # Delete in reverse order of dependency
            count_nav, _ = MutualFundNAV.objects.all().delete()
            count_perf, _ = MutualFundPerformance.objects.all().delete()
            count_schemes, _ = MutualFundScheme.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f"Successfully deleted {count_schemes} schemes, {count_nav} NAV records, and {count_perf} performance records."
        ))
