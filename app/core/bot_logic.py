# app/core/bot_logic.py
# ─────────────────────────────────────────────────────────────────────────────
# PLANTILLA DE LOGICA DE TRADING
# Adapta las condiciones de compra/venta segun tu estrategia real.
# ─────────────────────────────────────────────────────────────────────────────
import datetime

def decidir_operacion(current_price: float, tech_state: dict, config: dict,
                      df_cerradas=None, current_position=None,
                      buy_price: float = 0.0, bot_state: dict = None):
    """
    Motor principal de decision.
    Retorna: (accion, razon, precio, bot_state)
    accion puede ser: 'BUY' | 'SELL' | 'HOLD'
    """
    if bot_state is None:
        bot_state = {
            "daily_loss":    0.0,
            "last_trade_date": None,
            "win_history":   [],
        }

    if not tech_state:
        return "HOLD", "Sin datos tecnicos", current_price, bot_state

    # ── Reseteo diario ────────────────────────────────────────────────────
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    if bot_state.get("last_trade_date") != hoy:
        bot_state["daily_loss"]      = 0.0
        bot_state["last_trade_date"] = hoy

    # ── Limite de perdida diaria ──────────────────────────────────────────
    if bot_state.get("daily_loss", 0.0) >= 3.0:
        return ("HOLD",
                f"Limite diario alcanzado (-${bot_state['daily_loss']:.2f}).",
                current_price, bot_state)

    # ══════════════════════════════════════════════════════════════════════
    # LOGICA DE VENTA  (cuando ya estamos en posicion LONG)
    # ══════════════════════════════════════════════════════════════════════
    if current_position == "LONG" and buy_price > 0:
        tp_pct = config.get("tp_percent", 1.5)   # Take Profit %
        sl_pct = config.get("sl_percent", 0.5)   # Stop Loss %

        profit_pct = ((current_price - buy_price) / buy_price) * 100.0

        if profit_pct <= -sl_pct:
            bot_state.setdefault("win_history", []).append("LOSS")
            return "SELL", f"Stop Loss {sl_pct}% | Precio: {current_price:.2f}", current_price, bot_state

        if profit_pct >= tp_pct:
            bot_state.setdefault("win_history", []).append("WIN")
            return "SELL", f"Take Profit {tp_pct}% | Precio: {current_price:.2f}", current_price, bot_state

        signo = "+" if profit_pct >= 0 else ""
        return ("HOLD",
                f"LONG activo | Entrada: {buy_price:.2f} | PnL: {signo}{profit_pct:.2f}%",
                current_price, bot_state)

    # ══════════════════════════════════════════════════════════════════════
    # LOGICA DE COMPRA  (cuando no tenemos posicion)
    # Personaliza estas condiciones segun tu estrategia
    # ══════════════════════════════════════════════════════════════════════
    if current_position is None:
        rsi   = tech_state.get("rsi_val", 50) or 50
        ema_ok = tech_state.get("ema_alcista", False)

        # CONDICION DE EJEMPLO: RSI sobrevendido + tendencia alcista
        if rsi < config.get("rsi_oversold", 30) and ema_ok:
            return "BUY", f"Entrada | RSI={rsi:.1f} + EMA alcista | ${current_price:.2f}", current_price, bot_state

        return "HOLD", f"Esperando condicion | RSI={rsi:.1f}", current_price, bot_state

    return "HOLD", "Monitoreando...", current_price, bot_state
