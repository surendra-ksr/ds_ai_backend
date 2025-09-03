from django import forms

class ScreenerForm(forms.Form):
    """Form for filtering securities based on various criteria.
    """
    min_market_cap = forms.IntegerField(required=False, label="Min Market Cap (in Crores)")
    max_pe_ratio = forms.DecimalField(required=False, label="Max P/E Ratio")
    min_dividend_yield = forms.DecimalField(required=False, label="Min Dividend Yield (%)")

    sort_by = forms.ChoiceField(
        choices=[
            ('market_cap_desc', 'Market Cap: High to Low'),
            ('market_cap_asc', 'Market Cap: Low to High'),
            ('pe_ratio_asc', 'P/E Ratio: Low to High'),
            ('dividend_yield_desc', 'Dividend Yield: High to Low'),
        ],
        required=False,
        label="Sort By"
    )
