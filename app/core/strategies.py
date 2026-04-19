# app/core/strategies.py
# Define aqui tus estrategias de trading
# Agrega nuevas funciones o clases segun necesites
from app.utils.logger import setup_logger

logger = setup_logger("Strategy")

def run_strategy(symbol: str, strategy_name: str) -> str:
    """Ejecuta la estrategia seleccionada y devuelve un log de texto."""
    logger.info(f"Estrategia '{strategy_name}' en {symbol}")

    # ── Agrega tus estrategias aqui ──────────────────────────────────────
    if strategy_name == "RSI":
        return f"[RSI] {symbol}: Buscando niveles de sobrecompra/sobreventa."
    elif strategy_name == "MACD":
        return f"[MACD] {symbol}: Esperando cruce de lineas."
    elif strategy_name == "Grilla":
        return f"[Grilla] {symbol}: Grid Trading con rangos predefinidos."
    else:
        return f"Estrategia '{strategy_name}' no implementada aun."
