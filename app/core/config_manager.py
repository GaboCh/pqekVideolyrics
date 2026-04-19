# app/core/config_manager.py
# Carga y guarda la configuracion del bot desde app/bot_config.json
import json
import os

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "bot_config.json"
)

DEFAULT_CONFIG = {
    "symbol": "BTCUSDT",
    "interval": "1m",
    "tp_percent": 0.5,
    "sl_percent": 0.4,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "use_rsi": True,
    "use_ema": True,
    "use_bollinger": True,
    "paper_balance": 50.0,
    "live_capital": 50.0,
}

def load_bot_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                config.setdefault(k, v)
            return config
        except Exception:
            pass
    save_bot_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_bot_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True, "Configuracion guardada."
    except Exception as e:
        return False, f"Error: {e}"
