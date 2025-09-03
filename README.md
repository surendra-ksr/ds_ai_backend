# Dalal Street AI

Welcome to Dalal Street AI, a comprehensive platform for data-driven analysis and insights into the Indian financial markets. This project combines historical price analysis, real-time news sentiment, and machine learning to provide a holistic view of stocks and mutual funds.

---

## Features

- **Robust Data Pipeline**: A suite of powerful management commands to automatically fetch and process data for stocks, mutual funds, and news.
- **Advanced Analytical Core**: The backend can calculate key technical indicators (SMA, RSI, MACD, Bollinger Bands) and perform sentiment analysis on news articles.
- **Predictive Engine**: Includes both ARIMA and LSTM models to generate price forecasts.
- **Interactive Web Interface**: A clean, user-friendly UI built with Django and Chart.js, featuring:
    - A homepage listing all securities and mutual funds.
    - A detailed stock dashboard with zoomable candlestick and intraday charts, news, and predictions.
    - A detailed mutual fund page with a zoomable NAV chart and historical performance metrics.
- **REST API**: A well-structured API built with Django REST Framework to expose all backend data.

---

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL
- **Data Analysis**: Pandas, NumPy
- **Machine Learning**: Scikit-learn, TensorFlow, Statsmodels
- **Asynchronous Tasks**: Celery, Redis (planned, not yet implemented)
- **Frontend**: Django Templates, Chart.js

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
- **Add your database credentials and API keys** to the `.env` file:
  ```
  # .env
  SECRET_KEY='your-secret-key'
  NEWS_API_KEY='your-key-from-newsapi-org'
  MARKETAUX_API_KEY='your-key-from-marketaux'
  ```
- **Update the database settings** in `config/settings/base.py` to match your PostgreSQL setup.

### 3. Database Initialization

- **Create the database migrations**:
  ```sh
  python manage.py makemigrations
  ```
- **Apply the migrations** to create the database tables:
  ```sh
  python manage.py migrate
  ```
- **Seed the initial category data** (run this only once):
  ```sh
  python manage.py seed_categories
  ```

---

## Usage: The Automated Data Pipeline

Run these commands in order to populate your database with all the necessary data. All commands support progress bars.

1.  **Fetch All Stock Data**:
    ```sh
    python manage.py fetch_prices --all-major
    ```
2.  **Fetch All Mutual Fund Schemes**:
    ```sh
    python manage.py fetch_mf_schemes
    ```
3.  **Fetch All Mutual Fund Price History (NAV)**:
    ```sh
    python manage.py fetch_mf_navs --all
    ```
4.  **Calculate All Stock Indicators**:
    ```sh
    python manage.py calculate_indicators --all
    ```
5.  **Calculate All Mutual Fund Performance Metrics**:
    ```sh
    python manage.py calculate_mf_performance --all
    ```
6.  **Fetch News for All Stocks**:
    ```sh
    python manage.py fetch_news_sentiment --all
    ```
7.  **Generate Predictions for All Stocks**:
    ```sh
    python manage.py train_predict_arima --all
    ```
8.  **Fetch Intraday Data for All Stocks**:
    ```sh
    python manage.py fetch_intraday_prices --all
    ```

---

## Running the Application

1.  **Start the development server**:
    ```sh
    python manage.py runserver
    ```
2.  **Explore the application** in your browser:
    - **Homepage**: `http://127.0.0.1:8000/`
    - **Stock Detail**: `http://127.0.0.1:8000/securities/RELIANCE/`
    - **Mutual Funds**: `http://127.0.0.1:8000/mutual-funds/`
