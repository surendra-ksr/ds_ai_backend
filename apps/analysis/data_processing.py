import pandas as pd
import pandas_ta as ta
from apps.securities.models import Security, SecurityPrice, NewsArticle

def prepare_lstm_data(ticker):
    """
    Prepares a feature-rich DataFrame for a given security ticker, suitable for LSTM model training.

    Args:
        ticker (str): The ticker symbol of the security.

    Returns:
        pd.DataFrame: A DataFrame with price data, technical indicators, and aligned sentiment scores.
                     Returns None if there is not enough data.
    """
    try:
        security = Security.objects.get(ticker=ticker.upper())
    except Security.DoesNotExist:
        return None

    # 1. Fetch Price Data
    prices = SecurityPrice.objects.filter(security=security).order_by('date')
    if prices.count() < 60: # Need at least ~60 days for sequence models
        return None
    
    price_df = pd.DataFrame.from_records(prices.values('date', 'open', 'high', 'low', 'close', 'volume'))
    price_df['date'] = pd.to_datetime(price_df['date'])
    price_df.set_index('date', inplace=True)

    # 2. Fetch and Align Sentiment Data
    news = NewsArticle.objects.filter(security=security).order_by('published_at')
    if news.exists():
        news_df = pd.DataFrame.from_records(news.values('published_at', 'sentiment_score'))
        news_df['published_at'] = pd.to_datetime(news_df['published_at'])
        # Resample sentiment to a daily average, then calculate a rolling 7-day average to smooth it out
        daily_sentiment = news_df.set_index('published_at').resample('D').mean().fillna(0)
        daily_sentiment['sentiment_7d_ma'] = daily_sentiment['sentiment_score'].rolling(window=7).mean()
        # Merge sentiment into the main price DataFrame
        price_df = price_df.merge(daily_sentiment[['sentiment_7d_ma']], left_index=True, right_index=True, how='left')
        price_df['sentiment_7d_ma'].fillna(0, inplace=True)
    else:
        # If no news, just create a zero column
        price_df['sentiment_7d_ma'] = 0.0

    # 3. Feature Engineering: Technical Indicators and Volatility
    price_df.ta.sma(length=20, append=True)
    price_df.ta.ema(length=50, append=True)
    price_df.ta.rsi(length=14, append=True)
    price_df.ta.macd(append=True)
    price_df.ta.bbands(length=20, append=True) # Bollinger Bands for volatility

    # 4. Feature Engineering: Lagged Features
    for i in range(1, 8): # Create 7 days of lagged close prices
        price_df[f'close_lag_{i}'] = price_df['close'].shift(i)

    # Drop rows with NaN values created by indicators and lags
    price_df.dropna(inplace=True)

    # Ensure all data is float for the model
    price_df = price_df.astype(float)

    return price_df
