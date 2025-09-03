# Dalal Street AI

Welcome to Dalal Street AI, a comprehensive platform for data-driven analysis and insights into the Indian financial markets. This project combines historical price analysis, real-time news sentiment, and machine learning to provide a holistic view of stocks and mutual funds.

---

## Features

- **Robust Data Pipeline**: A suite of powerful management commands to automatically fetch and process data for stocks (historical & intraday), mutual funds (schemes & NAVs), and financial news.
- **Advanced Analytical Core**: The backend calculates key technical indicators (SMA, RSI, MACD, Bollinger Bands) and performs sentiment analysis on news articles using spaCy.
- **Dual Predictive Engine**: Includes two distinct predictive models:
    - A baseline **ARIMA** model for classical time-series forecasting.
    - An advanced **LSTM** neural network that incorporates price data, technical indicators, and news sentiment for a more holistic forecast.
- **Interactive Web Interface**: A clean, user-friendly UI built with Django and Chart.js, featuring:
    - A homepage listing all securities and mutual funds.
    - A detailed stock dashboard with zoomable, time-range-selectable candlestick charts, news, and dual model predictions.
    - A detailed mutual fund page with a zoomable NAV chart.
- **Full User Authentication & Watchlists**: Users can register, log in, and manage a personal watchlist of their favorite securities and mutual funds.
- **REST API**: A well-structured API built with Django REST Framework to expose all backend data and power the interactive frontend.

---

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL
- **Data Analysis**: Pandas, NumPy, spaCy
- **Machine Learning**: Scikit-learn, TensorFlow (Keras), Statsmodels
- **Frontend**: Django Templates, Bootstrap 5, Chart.js

---

## Project Setup and Installation

Follow these steps to get the project running locally.

### 1. Initial Setup

- **Clone the repository**.
- **Create and activate a virtual environment**:
  ```sh
  python -m venv venv
  # On Windows
  venv\Scripts\activate
  # On macOS/Linux
  source venv/bin/activate
  ```
- **Install dependencies**:
  ```sh
  pip install -r requirements.txt
  ```
- **Download NLP model**:
  ```sh
  python -m spacy download en_core_web_sm
  ```

### 2. Environment Configuration

- **Create a `.env` file** in the project root.
- **Add your database credentials and a secret key** to the `.env` file:
  ```
  # .env
  SECRET_KEY='your-django-secret-key'
  LOCAL_DB_PASSWORD='your-postgres-password'
  # Optional, for fetching live news
  NEWSDATA_API_KEY='your-key-from-newsdata.io'
  ```

### 3. Database Initialization

- **Apply the migrations** to create the database tables:
  ```sh
  python manage.py migrate
  ```
- **Seed the database with essential categories (Run this only once)**:
  ```sh
  python manage.py seed_categories
  ```

---

## Usage: Data Population and Model Training

Run these management commands to populate your database and train the predictive models. You can run them for individual tickers or use the `--all` flag where available.

1.  **Fetch Securities & Mutual Fund Schemes**:
    ```sh
    # Fetch a list of all major stocks
    python manage.py fetch_securities
    # Fetch a list of all mutual fund schemes (this will also update AUM and filter them)
    python manage.py fetch_mf_schemes
    ```
2.  **Fetch Historical Price Data**:
    ```sh
    # For all stocks
    python manage.py fetch_prices --all
    # For all mutual funds
    python manage.py fetch_mf_navs --all
    ```
3.  **Fetch News & Analyze Sentiment**:
    ```sh
    # For a specific stock (uses mock data if no API key is set)
    python manage.py fetch_news_articles --all
    ```
4.  **Train Predictive Models**:
    ```sh
    # Train the ARIMA model for a stock
    python manage.py train_predict_arima --all
    # Train the LSTM model for a stock
    python manage.py train_predict_lstm --all
    ```

---

## Running the Application

1.  **Start the development server**:
    ```sh
    python manage.py runserver
    ```
2.  **Explore the application** in your browser:
    - **Homepage**: `http://127.0.0.1:8000/`
    - **Register**: `http://127.0.0.1:8000/accounts/register/`
    - **Stock Detail**: `http://127.0.0.1:8000/securities/RELIANCE/`
    - **Mutual Funds**: `http://127.0.0.1:8000/mutual-funds/`
