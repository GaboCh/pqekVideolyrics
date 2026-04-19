# app/core/client.py
# Maneja la conexion con la API de Binance
from app.utils.config import load_binance_config
from app.utils.logger import setup_logger

logger = setup_logger("BinanceClient")

class BinanceCoreClient:
    def __init__(self):
        self.config = load_binance_config()
        self.api_key = self.config.get("api_key")

    def check_connection(self) -> str:
        if not self.api_key or "PEGA" in self.api_key or not self.api_key.strip():
            logger.warning("API Key no configurada")
            return "ERROR: Edita el archivo .env con tu API Key real de Binance."
        logger.info("API Key detectada - conexion lista")
        return "OK: API Key configurada correctamente."
