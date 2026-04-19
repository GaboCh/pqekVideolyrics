# app/utils/config.py
# Lee las variables de entorno desde el archivo .env
import os
from dotenv import load_dotenv

def load_binance_config() -> dict:
    load_dotenv()
    return {
        "api_key":    os.getenv("BINANCE_API_KEY", ""),
        "api_secret": os.getenv("BINANCE_SECRET_KEY", ""),
        "env":        os.getenv("APP_ENV", "development"),
    }
