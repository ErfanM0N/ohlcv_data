# AI Trading Bot - A Django-based Automated Trading System

This is a complete and fully functional Django application that serves as an automated trading bot for the Binance cryptocurrency exchange. It's designed to handle the entire trading workflow, from market data collection to position execution and tracking.

-----

## ✨ Key Features

  * **Automated Data Collection:** The bot automatically fetches **OHLCV (Open, High, Low, Close, Volume)** candle data from the Binance API and stores it in a database.
  * **Comprehensive API:** A robust RESTful API allows you to access market data and manage your trading activities programmatically.
  * **Automated Position Management:** The system can execute new trading positions, including pre-defined **Take Profit (TP)** and **Stop Loss (SL)** levels provided via the API.
  * **Real-time Tracking:** It actively monitors live positions, updating their status and outputting the results as they occur.

-----

## 🚀 Getting Started

### Prerequisites

  * Python 3.x
  * A Binance API key and secret.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ErfanM0N/ohlcv_data
    cd ohlcv_data
    ```
2.  **Set up your environment:**
    Create a virtual environment and install the required dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Configure API credentials:**
    Create a `.env` file in the project root and add your Binance API key and secret.
    ```env
    BINANCE_API_KEY="your_api_key_here"
    BINANCE_SECRET_KEY="your_secret_key_here"
    ```
4.  **Database setup:**
    Run the migrations to create the necessary database tables.
    ```bash
    python manage.py migrate
    ```
5.  **Run the application:**
    Start the Django development server to get the bot running.
    ```bash
    python manage.py runserver
    ```

-----
