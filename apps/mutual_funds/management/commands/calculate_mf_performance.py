import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from apps.mutual_funds.models import MutualFundScheme, MutualFundNAV, MutualFundPerformance
from datetime import date

def calculate_returns(nav_series):
    """Calculates various period returns from a series of NAVs."""
    if nav_series.empty:
        return {}

    today = nav_series.index[-1]
    performance = {}

    # Year-to-Date (YTD) Return
    start_of_year = nav_series.loc[f'{today.year}-01-01':].first_valid_index()
    if start_of_year is not None:
        ytd_start_nav = nav_series[start_of_year]
        ytd_end_nav = nav_series[today]
        performance['ytd_return'] = ((ytd_end_nav / ytd_start_nav) - 1) * 100

    # 1-Year, 3-Year, 5-Year Returns
    for years in [1, 3, 5]:
        start_date = today - pd.DateOffset(years=years)
        # Find the closest available date in the index
        actual_start_date = nav_series.index.asof(start_date)
        if actual_start_date is not None:
            start_nav = nav_series[actual_start_date]
            end_nav = nav_series[today]
            # Annualize the return
            annualized_return = (((end_nav / start_nav) ** (1 / years)) - 1) * 100
            performance[f'return_{years}y'] = annualized_return

    return performance

class Command(BaseCommand):
    help = 'Calculates historical performance metrics for all mutual fund schemes.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Process all mutual fund schemes.')

    def handle(self, *args, **options):
        if not options['all']:
            raise CommandError("This command now only supports the --all flag.")

        schemes = MutualFundScheme.objects.all()
        self.stdout.write(self.style.SUCCESS(f"Calculating performance for {schemes.count()} mutual fund schemes..."))

        for scheme in tqdm(schemes, desc="Calculating MF Performance"):
            navs = MutualFundNAV.objects.filter(scheme=scheme).order_by('date').values_list('date', 'nav')
            if navs.count() < 2: # Need at least two data points to calculate a return
                continue

            # Create a pandas Series for easy calculation
            dates = [n[0] for n in navs]
            values = [float(n[1]) for n in navs]
            nav_series = pd.Series(values, index=pd.to_datetime(dates))

            # Calculate performance
            performance_data = calculate_returns(nav_series)

            # Save to the database
            if performance_data:
                MutualFundPerformance.objects.update_or_create(
                    scheme=scheme,
                    defaults=performance_data
                )

        self.stdout.write(self.style.SUCCESS("\nMutual fund performance calculation complete."))
