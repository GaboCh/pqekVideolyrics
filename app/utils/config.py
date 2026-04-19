# app/utils/config.py
# Lee las variables de entorno desde el archivo .env
import os
from dotenv import load_dotenv

def load_app_config() -> dict:
    load_dotenv()
    return {
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        "app_env":      os.getenv("APP_ENV", "development"),
    }
