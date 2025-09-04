import pandas as pd
from apps.securities.models import Security, SecurityPrice, NewsArticle

# --- Helper function for RSI calculation ---
def _calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def prepare_lstm_data(ticker):
    """
    Prepares a feature-rich DataFrame for a given security ticker, suitable for LSTM model training.
    This function no longer uses pandas-ta to ensure cross-platform compatibility.
    """
    try:
        security = Security.objects.get(ticker=ticker.upper())
    except Security.DoesNotExist:
        return None

    # 1. Fetch Price Data
    prices = SecurityPrice.objects.filter(security=security).order_by('date')
    if prices.count() < 60:
        return None
    
    price_df = pd.DataFrame.from_records(prices.values('date', 'open', 'high', 'low', 'close', 'volume'))
    price_df['date'] = pd.to_datetime(price_df['date'])
    price_df.set_index('date', inplace=True)

    # 2. Fetch and Align Sentiment Data
    news = NewsArticle.objects.filter(security=security).order_by('published_at')
    if news.exists():
        news_df = pd.DataFrame.from_records(news.values('published_at', 'sentiment_score'))
        news_df['published_at'] = pd.to_datetime(news_df['published_at'])
        daily_sentiment = news_df.set_index('published_at').resample('D').mean().fillna(0)
        daily_sentiment['sentiment_7d_ma'] = daily_sentiment['sentiment_score'].rolling(window=7).mean()
        price_df = price_df.merge(daily_sentiment[['sentiment_7d_ma']], left_index=True, right_index=True, how='left')
        price_df['sentiment_7d_ma'].fillna(0, inplace=True)
    else:
        price_df['sentiment_7d_ma'] = 0.0

    # 3. Manual Technical Indicator Calculation
    price_df['SMA_20'] = price_df['close'].rolling(window=20).mean()
    price_df['EMA_50'] = price_df['close'].ewm(span=50, adjust=False).mean()
    price_df['RSI_14'] = _calculate_rsi(price_df['close'])

    ema_12 = price_df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = price_df['close'].ewm(span=26, adjust=False).mean()
    price_df['MACD_12_26_9'] = ema_12 - ema_26
    price_df['MACDs_12_26_9'] = price_df['MACD_12_26_9'].ewm(span=9, adjust=False).mean()

    # 4. Feature Engineering: Lagged Features
    for i in range(1, 8):
        price_df[f'close_lag_{i}'] = price_df['close'].shift(i)

    # Drop rows with NaN values created by indicators and lags
    price_df.dropna(inplace=True)

    # Ensure all data is float for the model
    price_df = price_df.astype(float)

    return price_df
