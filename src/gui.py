import gradio as gr
import os
import sys
import subprocess
import time
import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from app.core.data_fetcher import fetch_klines
from app.core.chart_visualizer import create_candlestick_chart
from app.core.technical_analysis import analyze_latest_patterns, get_technical_state
from app.core.bot_logic import decidir_operacion
from app.core.config_manager import load_bot_config, save_bot_config

import platform

load_dotenv()

# ==========================================
# LOGGER: bot_log.txt
# ==========================================
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot_log.txt")

def escribir_log_txt(mensaje):
    """Escribe una línea en bot_log.txt con hora."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {mensaje}\n")

def limpiar_logs():
    """Borra el contenido del log y escribe cabecera de sesión."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"--- INICIO DE SESIÓN ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---\n")
    return "✅ Logs limpiados correctamente."

def abrir_carpeta_logs():
    """Abre en el explorador la carpeta donde está bot_log.txt."""
    ruta = os.path.dirname(LOG_FILE) or os.getcwd()
    try:
        if platform.system() == "Windows":
            os.startfile(ruta)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta])
        return f"✅ Carpeta abierta: {ruta}"
    except Exception as e:
        return f"❌ Error al abrir carpeta: {e}"

# ==========================================
# ESTADO GLOBAL
# ==========================================
widget_process = None
bot_config = load_bot_config()

# ==========================================
# LÓGICA: WIDGET
# ==========================================
def toggle_widget(action):
    global widget_process
    if action == "Abrir":
        if widget_process is None or widget_process.poll() is not None:
            widget_process = subprocess.Popen([sys.executable, "run_widget.py"])
            return "✅ Widget Abierto."
        else:
            return "⚠️ El widget ya está abierto."
    else:
        if widget_process is not None and widget_process.poll() is None:
            widget_process.terminate()
            widget_process = None
            return "⛔ Widget Cerrado."
        else:
            return "⚠️ El widget ya estaba cerrado."

import json
def save_widget_config(symbols):
    try:
        with open("widget_config.json", "w", encoding="utf-8") as f:
            json.dump({"symbols": symbols}, f)
        return "¡Configuración guardada EXITOSAMENTE! El Widget se actualizará al instante."
    except Exception as e:
        return f"Error guardando: {e}"

# ==========================================
# LÓGICA: PESTAÑA 1 (DASHBOARD)
# ==========================================
def render_chart(symbol):
    try:
        df = fetch_klines(symbol=symbol, interval=bot_config.get("interval", "1m"), limit=100)
        mensaje, annotations = analyze_latest_patterns(df)
        texto_final = f"### 🤖 Tu Analizador Automático te informa sobre **{symbol}**:\n\n{mensaje}"
        fig = create_candlestick_chart(df, symbol=symbol, annotations_list=annotations)
        return fig, texto_final
    except Exception as e:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(text=f"Error cargando grafico: {str(e)}", showarrow=False, font=dict(size=20))
        return fig, "Ocurrió un error leyendo el gráfico."

# ==========================================
# LÓGICA: PESTAÑA 4 (CONFIGURACIÓN)
# ==========================================
def save_settings(symbol, interval, tp, sl, rsi_ob, rsi_os, u_rsi, u_ema, u_bollinger, u_sch, sch_start, sch_end):
    global bot_config
    bot_config.update({
        "symbol": symbol,
        "interval": interval,
        "tp_percent": tp,
        "sl_percent": sl,
        "rsi_overbought": rsi_ob,
        "rsi_oversold": rsi_os,
        "use_rsi": u_rsi,
        "use_ema": u_ema,
        "use_bollinger": u_bollinger,
        "use_schedule": u_sch,
        "schedule_start_utc": sch_start,
        "schedule_end_utc": sch_end
    })
    success, msg = save_bot_config(bot_config)
    return f"✅ {msg}\nNuevos parámetros listos para usarse en Laboratorio y Producción."


# ==========================================
# LÓGICA: PESTAÑA 2 (LAB PROCEDIMIENTOS)
# ==========================================
import threading

is_simulation_running = False
background_bot_thread = None
global_trade_history = []
ui_shared_state = {
    "status": "Inactivo", "saldo": 0.0, "posicion": "Ninguna", "pnl": 0.0,
    "rendimiento_log": "Esperando datos...", "t_ops": "0", "t_wr": "0.0%", 
    "t_wl": "0 / 0", "t_pf": "0.00", "t_aw": "$0.00", "t_al": "$0.00", 
    "t_rw": "0", "t_rl": "0"
}

def stop_paper_simulation():
    global is_simulation_running
    is_simulation_running = False
    return "Deteniendo simulación..."

def bot_engine_loop():
    global bot_config, is_simulation_running, global_trade_history, ui_shared_state
    
    symbol = bot_config.get("symbol", "BTCUSDT")
    interval = bot_config.get("interval", "1m")
    
    bot_state = {
        "daily_loss": 0.0, "last_trade_date": None, "trade_history": [],
        "total_trades": 0, "win_trades": 0, "racha_ganadora": 0, "racha_perdedora": 0,
        "max_racha_ganadora": 0, "max_racha_perdedora": 0, "win_history": []
    }
    
    COOLDOWN_VELAS = 5        # Regla 3: 5 velas de castigo tras cualquier venta
    
    # Calcular duración del intervalo en segundos para el cooldown basado en tiempo
    _interval_map = {"1m": 60, "3m": 180, "5m": 300, "15m": 900, "1h": 3600}
    INTERVALO_SEG = _interval_map.get(interval, 60)
    
    historial = []
    saldo = bot_config.get("paper_balance", 100.0)
    saldo_inicial = saldo
    posicion = None
    buy_price = 0.0
    cantidad_comprada = 0.0
    tiempo_fin_cooldown = 0     # Timestamp en segundos hasta cuando dura el cooldown
    orden_limit_pendiente = False  # Estado: hay una orden LIMIT virtual activa
    precio_limit_compra = 0.0      # Precio objetivo de la orden LIMIT
    orden_limit_ts = 0.0           # Timestamp cuando se colocó la orden LIMIT
    
    while is_simulation_running:
        try:
            if len(df_full := fetch_klines(symbol=symbol, interval=interval, limit=100)) < 2:
                time.sleep(5)
                continue

            # ============================================================
            # PRECIO VIVO: solo para monitorear TP/SL en posición abierta
            # TECH STATE:  calculado sobre VELAS CERRADAS (iloc[:-1])
            # Esto elimina el ruido de la vela que aún se está formando
            # ============================================================
            precio_actual_vivo = float(df_full['close'].iloc[-1])
            df_cerradas = df_full.iloc[:-1].copy()
            df_cerradas, tech_state = get_technical_state(df_cerradas)
            if tech_state is None:
                time.sleep(5)
                continue

            # Cooldown basado en tiempo (más robusto que contar velas)
            tiempo_actual = time.time()
            en_cooldown = tiempo_actual < tiempo_fin_cooldown
            secs_restantes = max(0, int(tiempo_fin_cooldown - tiempo_actual))
            velas_restantes = (secs_restantes // INTERVALO_SEG) + (1 if secs_restantes % INTERVALO_SEG else 0)

            accion, motivo, precio_actual, bot_state = decidir_operacion(
                current_price=precio_actual_vivo, tech_state=tech_state,
                config=bot_config, df_cerradas=df_cerradas,
                current_position=posicion,
                buy_price=buy_price, bot_state=bot_state
            )
            
            # Si hay cooldown activo, bloquear COMPRAS (pero no ventas)
            if en_cooldown and accion == "BUY":
                accion = "HOLD"
                motivo = f"❄️ COOLDOWN ACTIVO — Faltan ~{velas_restantes} velas ({secs_restantes}s) para volver a comprar."
            
            # --- LOG DIAGNÓSTICO COMPLETO: una vez por vela nueva en estado IDLE ---
            if posicion is None and not orden_limit_pendiente:
                rsi_v    = tech_state.get("rsi_val", 0)
                boll_piso = tech_state.get("bollinger_toque_piso", False)
                ema_al   = tech_state.get("ema_alcista", False)
                rsi_rec  = tech_state.get("rsi_recuperandose", False)
                v_a      = tech_state.get("volumen_actual", 0)
                v_p      = tech_state.get("volumen_promedio_5", 1)
                pat      = tech_state.get("patrones", {})
                patron_ok = not (pat.get("doji", False) or pat.get("engulfing_bear", False))
                # Condiciones MODO A
                cond_rsi_a = rsi_v < 40
                cond_bol_a = boll_piso
                cond_vol_a = v_a >= v_p * 0.7
                modo_a_ok  = cond_rsi_a and cond_bol_a and cond_vol_a and patron_ok
                # Condiciones MODO B
                cond_ema_b = ema_al
                cond_rsi_b = 40 <= rsi_v <= 60 and rsi_rec
                cond_vol_b = v_a >= v_p * 0.4
                modo_b_ok  = cond_ema_b and cond_rsi_b and cond_vol_b and patron_ok
                vol_ratio  = v_a / v_p if v_p > 0 else 0
                tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                diag = (
                    f"[{tiempo_str}] Precio: ${precio_actual_vivo:.0f} | "
                    f"MODO A: RSI({rsi_v:.1f}) {'✅' if cond_rsi_a else '❌'} "
                    f"BollPiso {'✅' if cond_bol_a else '❌'} "
                    f"Vol({v_a:.0f}/{v_p:.0f}={vol_ratio:.2f}) {'✅' if cond_vol_a else '❌'} "
                    f"Patrones: OK {'✅' if patron_ok else '❌'} → {'🟢' if modo_a_ok else 'NO'} | "
                    f"MODO B: EMA {'✅' if cond_ema_b else '❌'} "
                    f"RSI({rsi_v:.1f}) {'✅' if cond_rsi_b else '❌'} "
                    f"Vol({v_a:.0f}/{v_p:.0f}={vol_ratio:.2f}) {'✅' if cond_vol_b else '❌'} "
                    f"Patrones: OK {'✅' if patron_ok else '❌'} → {'🟢' if modo_b_ok else 'NO'} | → HOLD"
                )
                print(diag)
                escribir_log_txt(diag)
                historial.append(diag)  # Acumula sin límite en la UI
            
            # ============================================================
            # MÁQUINA DE ESTADOS: ORDEN LIMIT SIMULADA
            #
            #  IDLE     → señal BUY  → PENDING (orden colocada al precio cierre)
            #  PENDING  → precio toca/baja → LONG (fill a precio_limit_compra, 0 slippage)
            #  PENDING  → timeout 3 velas  → IDLE (orden cancelada, mercado se fue)
            #  LONG     → señal SELL        → IDLE (venta a precio vivo, comisión Taker)
            # ============================================================

            # --- ESTADO PENDING: chequear fill o timeout ANTES de evaluar nuevas señales ---
            if orden_limit_pendiente and posicion is None:
                velas_desde_orden = (time.time() - orden_limit_ts) / INTERVALO_SEG
                if precio_actual_vivo <= precio_limit_compra:
                    # ✅ FILL: el precio bajó y tocó nuestra orden
                    usdt_in = max(5.0, saldo * 0.15)     # 15% del saldo, mínimo $5
                    comision_usdt = usdt_in * 0.0008     # Maker fee 0.08%
                    usdt_after_fee = usdt_in - comision_usdt
                    cantidad_comprada = usdt_after_fee / precio_limit_compra
                    saldo -= usdt_in
                    posicion = "LONG"
                    buy_price = precio_limit_compra      # 0 slippage
                    bot_state['buy_comision_usdt'] = comision_usdt
                    bot_state['buy_slippage_usdt'] = 0.0
                    orden_limit_pendiente = False
                    tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                    msg_fill = f"✅ LIMIT FILLED {symbol} | REBOTE | ${usdt_in:.2f} a ${buy_price:,.2f} | Com(Maker): -${comision_usdt:.4f}"
                    historial.insert(0, f"[{tiempo_str}] {msg_fill}")
                    escribir_log_txt(msg_fill)
                elif velas_desde_orden >= 3:
                    # ⏰ TIMEOUT: el mercado subió sin nosotros, cancelar
                    orden_limit_pendiente = False
                    tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                    msg_cancel = f"⏰ LIMIT CANCELADA (timeout 3 velas) | Objetivo era ${precio_limit_compra:,.2f} | Precio actual ${precio_actual_vivo:,.2f}"
                    historial.insert(0, f"[{tiempo_str}] {msg_cancel}")
                    escribir_log_txt(msg_cancel)
                else:
                    tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                    velas_espera = 3 - int(velas_desde_orden)
                    ui_shared_state["status"] = f"⏳ Orden LIMIT pendiente a ${precio_limit_compra:,.2f} | Precio vivo ${precio_actual_vivo:,.2f} | Timeout en ~{velas_espera} velas"

            # --- SEÑAL DE DECISIÓN (solo si no hay orden pendiente ni posición abierta) ---
            if not orden_limit_pendiente and posicion is None:
                if accion == "BUY" and not en_cooldown:
                    monto_trade = max(5.0, saldo * 0.15)  # 15% del saldo
                    if saldo < monto_trade:
                        tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                        historial.insert(0, f"[{tiempo_str}] ⚠️ Saldo insuficiente (${saldo:.2f}) para trade del 15%")
                    else:
                        # Colocar orden LIMIT al precio de cierre de la última vela cerrada
                        precio_limit_compra = float(df_cerradas['close'].iloc[-1])
                        orden_limit_pendiente = True
                        orden_limit_ts = time.time()
                        bot_state['modo_entrada'] = "REBOTE"
                        tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                        msg_limit = f"📋 ORDEN LIMIT COLOCADA | REBOTE ({monto_trade:.2f} USDT) | Comprando si precio ≤ ${precio_limit_compra:,.2f}"
                        historial.insert(0, f"[{tiempo_str}] {msg_limit}")
                        escribir_log_txt(msg_limit)

            # --- ESTADO LONG: gestión de la posición (TP/SL/Trailing a precio vivo) ---
            elif accion == "SELL" and posicion == "LONG":
                sell_price = precio_actual_vivo                      # Taker: precio de mercado
                venta_bruta = cantidad_comprada * sell_price
                comision_usdt = venta_bruta * 0.001                  # Taker fee 0.10%
                venta_neta = venta_bruta - comision_usdt
                ganancia_bruta = venta_bruta - (cantidad_comprada * buy_price)
                inversion_inicial_trade = (cantidad_comprada * buy_price) / (1 - 0.0008)
                ganancia_neta = venta_neta - inversion_inicial_trade
                total_slippage = 0.0                                 # Compra fue Maker, 0 slippage
                total_comision = bot_state.get('buy_comision_usdt', 0) + comision_usdt
                saldo += venta_neta
                posicion = None
                tiempo_fin_cooldown = time.time() + (COOLDOWN_VELAS * INTERVALO_SEG)
                
                if ganancia_neta < 0:
                    bot_state['daily_loss'] += abs(ganancia_neta)
                    bot_state['racha_perdedora'] = bot_state.get('racha_perdedora', 0) + 1
                    bot_state['racha_ganadora'] = 0
                else:
                    bot_state['racha_ganadora'] = bot_state.get('racha_ganadora', 0) + 1
                    bot_state['racha_perdedora'] = 0
                bot_state['total_trades'] += 1
                if ganancia_neta > 0: bot_state['win_trades'] += 1
                tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                log_str = (f"[{tiempo_str}] 🔴 VENTA | {motivo}\n"
                           f"Bruto: ${ganancia_bruta:.3f} | Com: -${total_comision:.4f} | Neto: ${ganancia_neta:.3f} | ❄️ Cooldown: {COOLDOWN_VELAS} velas")
                historial.insert(0, log_str)
                escribir_log_txt(f"🔴 VENTA | {motivo} | Bruto: ${ganancia_bruta:.3f} | Neto: ${ganancia_neta:.3f}")
                
                trade_record = {
                    "fecha_venta": tiempo_str, "modo": bot_state.get('modo_entrada', "N/A"),
                    "compra_p": buy_price, "venta_p": sell_price, "motivo": motivo,
                    "g_bruta": ganancia_bruta, "comision": total_comision, "slippage": total_slippage,
                    "g_neta": ganancia_neta, "saldo": saldo
                }
                bot_state['trade_history'].append(trade_record)
                global_trade_history.append(trade_record)
                bot_state['max_racha_ganadora'] = max(bot_state.get('max_racha_ganadora', 0), bot_state['racha_ganadora'])
                bot_state['max_racha_perdedora'] = max(bot_state.get('max_racha_perdedora', 0), bot_state['racha_perdedora'])
                buy_price = 0.0
                cantidad_comprada = 0.0
                
            elif accion == "HOLD":
                tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                if "Límite Diario" in motivo or "Win Rate" in motivo:
                    if not historial or not historial[0].startswith("⚠️ SUSPENSIÓN"):
                        historial.insert(0, f"[{tiempo_str}] ⚠️ SUSPENSIÓN DE SEGURIDAD: {motivo}")
                else:
                    historial.insert(0, f"[{tiempo_str}] {motivo}")

            # Sin límite de líneas — historial completo de la sesión
                    
            estado_pos = f"COMPRADO a ${buy_price:.2f}" if posicion else "SIN POSICIÓN"
            pnl = saldo - saldo_inicial
            if posicion == "LONG":
                valor_actual_inversion = cantidad_comprada * precio_actual
                pnl = (saldo + valor_actual_inversion) - saldo_inicial
            
            color_pnl = "🟩" if pnl >= 0 else "🟥"
            rendimiento = f"{color_pnl} Rendimiento de la sesión en vivo: ${pnl:.2f} USDT"
            log_txt = "\n".join(historial) if historial else f"Monitoreando velas de {symbol} en vivo... Sin operaciones."
            
            total_ops = bot_state.get('total_trades', 0)
            wins = bot_state.get('win_trades', 0)
            losses = total_ops - wins
            sum_wins = sum(t['g_neta'] for t in bot_state['trade_history'] if isinstance(t, dict) and t.get('g_neta', 0) > 0)
            sum_losses = sum(abs(t['g_neta']) for t in bot_state['trade_history'] if isinstance(t, dict) and t.get('g_neta', 0) < 0)
            
            ui_shared_state.update({
                "status": f"🟢 Simulación EN VIVO. Último precio: ${precio_actual:.2f}",
                "saldo": saldo if posicion is None else (saldo + cantidad_comprada*precio_actual),
                "posicion": estado_pos, "pnl": pnl, "rendimiento_log": rendimiento + "\n\n--- Historial ---\n" + log_txt,
                "t_ops": str(total_ops), "t_wr": f"{(wins/total_ops*100):.1f}%" if total_ops > 0 else "0.0%",
                "t_wl": f"{wins} / {losses}", "t_pf": f"{(sum_wins / sum_losses) if sum_losses > 0 else (sum_wins if sum_wins > 0 else 0.0):.2f}",
                "t_aw": f"${(sum_wins / wins) if wins > 0 else 0.0:.3f}", "t_al": f"-${(sum_losses / losses) if losses > 0 else 0.0:.3f}",
                "t_rw": str(bot_state.get('max_racha_ganadora', 0)), "t_rl": str(bot_state.get('max_racha_perdedora', 0))
            })
            
        except Exception as e:
            ui_shared_state["status"] = f"Error descargando datos: {e}"
            time.sleep(5)
            continue
            
        # Esperar ~30 segundos antes del próximo ciclo (verifica si la vela cerró)
        for _ in range(30):
            if not is_simulation_running: break
            time.sleep(1)



def run_paper_simulation():
    global is_simulation_running, background_bot_thread, ui_shared_state, bot_config, global_trade_history
    
    if not is_simulation_running:
        is_simulation_running = True
        global_trade_history = []
        ui_shared_state["saldo"] = bot_config.get("paper_balance", 100.0)
        limpiar_logs()  # Auto-limpia el log en cada nueva sesión
        escribir_log_txt(f"Iniciando simulación | Par: {bot_config.get('symbol','BTCUSDT')} | Intervalo: {bot_config.get('interval','1m')}")
        background_bot_thread = threading.Thread(target=bot_engine_loop, daemon=True)
        background_bot_thread.start()
        
    while is_simulation_running:
        yield (
            ui_shared_state["status"], ui_shared_state["saldo"], ui_shared_state["posicion"],
            ui_shared_state["pnl"], ui_shared_state["rendimiento_log"], ui_shared_state["t_ops"],
            ui_shared_state["t_wr"], ui_shared_state["t_wl"], ui_shared_state["t_pf"],
            ui_shared_state["t_aw"], ui_shared_state["t_al"], ui_shared_state["t_rw"], ui_shared_state["t_rl"]
        )
        time.sleep(1) 
        
    yield (
        "🔴 Simulación Detenida por el Usuario.", ui_shared_state["saldo"], ui_shared_state["posicion"],
        ui_shared_state["pnl"], ui_shared_state["rendimiento_log"], ui_shared_state["t_ops"],
        ui_shared_state["t_wr"], ui_shared_state["t_wl"], ui_shared_state["t_pf"],
        ui_shared_state["t_aw"], ui_shared_state["t_al"], ui_shared_state["t_rw"], ui_shared_state["t_rl"]
    )

def exportar_csv():
    global global_trade_history
    if not global_trade_history:
        # Crea archivo vacio para que no crashee
        df = pd.DataFrame(columns=["Vacio"])
        df.to_csv("historial_vacio.csv", index=False)
        return "historial_vacio.csv"
        
    df = pd.DataFrame(global_trade_history)
    df.to_csv("historial_operaciones_scapling.csv", index=False)
    return "historial_operaciones_scapling.csv"

def promover_a_produccion():
    # Desbloquea la pestaña 3
    return gr.update(interactive=True, value="🟢 PRODUCCIÓN DESBLOQUEADA"), gr.update(visible=True)


# ==========================================
# LÓGICA: PESTAÑA 3 (PRODUCCIÓN)
# ==========================================
# En la vida real, el flag global indicará si el bot está prendido
is_live_bot_running = False

def toggle_live_bot(api_key, api_secret, capital, is_running_state):
    global is_live_bot_running, bot_config
    if is_running_state:
        # Apagamos
        is_live_bot_running = False
        return False, "Bot Real Apagado. Dinero a salvo.", "🔴 APAGADO"
    else:
        if not api_key or not api_secret:
            return False, "Faltan credenciales API.", "🔴 ERROR"
        
        # Validar capital
        try:
            cap = float(capital)
            if cap <= 0: raise ValueError
        except:
            return False, "Capital inválido. Ingresa un número mayor a 0.", "🔴 ERROR"
        
        is_live_bot_running = True
        log = f"🚀 Bot iniciando en Binance... Par: {bot_config['symbol']} | Capital: {cap} USDT"
        return True, log, "🟢 BOT ACTIVO"

def panic_sell(api_key, api_secret):
    global is_live_bot_running
    is_live_bot_running = False
    return False, "🚨 ¡PÁNICO! Bot detenido. Orden de MARKET SELL enviada a Binance.", "🔴 APAGADO"


# ==========================================
# CONSTRUIR INTERFAZ GRADIO
# ==========================================
dark_theme = gr.themes.Monochrome(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
).set(
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_400",
)

with gr.Blocks(title="Antigravity Binance Bot", theme=dark_theme) as app:
    gr.Markdown("# 🚀 Antigravity Binance Trading Bot")
    
    with gr.Tabs():
        # ---------------------------------------------
        # PESTAÑA 1: DASHBOARD
        # ---------------------------------------------
        with gr.Tab("1. Dashboard Global"):
            gr.Markdown("Visualiza el análisis del mercado en vivo.")
            with gr.Row():
                chart_symbol = gr.Dropdown(["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "SIRENUSDT"], label="Par de Monedas", value=bot_config.get("symbol", "BTCUSDT"), allow_custom_value=True)
                chart_btn = gr.Button("📊 Dibujar Velas e Interpretar", variant="primary")
                
            plot_output = gr.Plot()
            interpretation_output = gr.Markdown("Toca el botón para analizar el gráfico en automático.")
            
            chart_btn.click(fn=render_chart, inputs=[chart_symbol], outputs=[plot_output, interpretation_output])
            
        # ---------------------------------------------
        # PESTAÑA 2: LABORATORIO (PAPER TRADING)
        # ---------------------------------------------
        with gr.Tab("2. Laboratorio (Paper Trading)"):
            gr.Markdown("### 🧪 Laboratorio de Pruebas Seguras")
            gr.Markdown("El bot operará usando matemáticas contra datos reales y recientes de Binance, **pero usando dinero ficticio**.")
            
            with gr.Row():
                lab_status = gr.Textbox(label="Estado del Laboratorio", value="Inactivo", interactive=False)
                lab_balance = gr.Number(label="Saldo Ficticio (USDT)", value=bot_config.get("paper_balance", 50), interactive=False)
                lab_pos = gr.Textbox(label="Posición Abierta", value="Ninguna", interactive=False)
                lab_pnl = gr.Number(label="PnL (Beneficio/Pérdida)", value=0.0, interactive=False)
                
            gr.Markdown("#### 📈 Dashboard Avanzado de Estadísticas")
            with gr.Row():
                st_trades = gr.Textbox(label="Op. Totales", value="0", interactive=False)
                st_winrate = gr.Textbox(label="Win Rate %", value="0.0%", interactive=False)
                st_wl = gr.Textbox(label="Victorias / Derrotas", value="0 / 0", interactive=False)
                st_profit_factor = gr.Textbox(label="Profit Factor", value="0.00", interactive=False)
            with gr.Row():
                st_avg_w = gr.Textbox(label="Ganancia Promedio", value="$0.00", interactive=False)
                st_avg_l = gr.Textbox(label="Pérdida Promedio", value="$0.00", interactive=False)
                st_streak_w = gr.Textbox(label="Mejor Racha", value="0", interactive=False)
                st_streak_l = gr.Textbox(label="Peor Racha", value="0", interactive=False)
                
            with gr.Row():
                btn_start_sim = gr.Button("▶️ Iniciar Simulación en VIVO", variant="primary")
                btn_stop_sim = gr.Button("🛑 Detener Simulación", variant="stop")
                btn_csv = gr.Button("⬇️ Exportar CSV")
                btn_promote = gr.Button("⭐ Promover a Producción ⭐", variant="secondary")
                
            with gr.Row():
                btn_abrir_carpeta = gr.Button("📂 Abrir Carpeta de Logs", variant="secondary")
                btn_limpiar_logs = gr.Button("🗑️ Limpiar bot_log.txt", variant="secondary")
                log_util_status = gr.Textbox(label="Estado", interactive=False, scale=3)
                
            file_csv = gr.File(label="Descarga", interactive=False)
            lab_log = gr.Textbox(label="Rendimiento e Historial de Trades", lines=12, interactive=False)
            
            out_comps = [lab_status, lab_balance, lab_pos, lab_pnl, lab_log,
                         st_trades, st_winrate, st_wl, st_profit_factor,
                         st_avg_w, st_avg_l, st_streak_w, st_streak_l]
            
            # Conectar la simulación
            btn_start_sim.click(fn=run_paper_simulation, inputs=[], outputs=out_comps)
            btn_stop_sim.click(fn=stop_paper_simulation, inputs=[], outputs=[lab_status])
            btn_csv.click(fn=exportar_csv, inputs=[], outputs=[file_csv])
            btn_abrir_carpeta.click(fn=abrir_carpeta_logs, inputs=[], outputs=[log_util_status])
            btn_limpiar_logs.click(fn=limpiar_logs, inputs=[], outputs=[log_util_status])

        # ---------------------------------------------
        # PESTAÑA 3: PRODUCCIÓN (REAL)
        # ---------------------------------------------
        with gr.Tab("3. Producción (Trading Real)"):
            gr.Markdown("### ⚠️ ENTORNO REAL DE TRADING - ¡Lee esto!")
            gr.Markdown("**MANDATORIO:** Solo puedes usar este entorno después de validar tu estrategia en el Laboratorio.")
            
            # Bloqueo Visual
            unlock_status = gr.Textbox(label="Estado de Producción", value="🔴 BLOQUEADO (Ve al Laboratorio y haz clic en Promover)", interactive=False)
            
            with gr.Column(visible=False) as prod_container:
                with gr.Row():
                    api_key_input = gr.Textbox(label="Binance API Key", type="password")
                    api_secret_input = gr.Textbox(label="Binance API Secret", type="password")
                    capital_input = gr.Number(label="Capital Real a arriesgar (USDT)", value=50.0)
                
                with gr.Row():
                    prod_toggle_state = gr.State(False) # Track if running
                    btn_toggle_bot = gr.Button("🟢 ENCENDER BOT (Doble Confirmación)", variant="primary")
                    btn_panic = gr.Button("🚨 BOTÓN DE PÁNICO (Vender Todo Ya)", variant="stop")
                    
                prod_log = gr.Textbox(label="Log en vivo de BINANCE REAL", lines=10, interactive=False)
                
                # Acciones Producción
                btn_toggle_bot.click(
                    fn=toggle_live_bot,
                    inputs=[api_key_input, api_secret_input, capital_input, prod_toggle_state],
                    outputs=[prod_toggle_state, prod_log, btn_toggle_bot]
                )
                
                btn_panic.click(
                    fn=panic_sell,
                    inputs=[api_key_input, api_secret_input],
                    outputs=[prod_toggle_state, prod_log, btn_toggle_bot]
                )

            # Acoplar el botón promover de la pestaña 2 con el desbloqueo
            btn_promote.click(
                fn=promover_a_produccion,
                inputs=[],
                outputs=[unlock_status, prod_container]
            )

        # ---------------------------------------------
        # PESTAÑA 4: CONFIGURACIÓN GENERAL
        # ---------------------------------------------
        with gr.Tab("4. Configuración del Bot"):
            gr.Markdown("### ⚙️ Reglas Centrales y Parámetros")
            with gr.Row():
                cfg_symbol = gr.Dropdown(["BTCUSDT", "ETHUSDT", "SOLUSDT"], value=bot_config.get("symbol", "BTCUSDT"), label="Par Principal")
                cfg_interval = gr.Dropdown(["1m", "5m", "15m", "1h"], value=bot_config.get("interval", "5m"), label="Temporalidad de Velas")
                
            with gr.Row():
                cfg_tp = gr.Slider(minimum=0.1, maximum=10.0, step=0.1, value=bot_config.get("tp_percent", 0.5), label="Take-Profit %")
                cfg_sl = gr.Slider(minimum=0.1, maximum=10.0, step=0.1, value=bot_config.get("sl_percent", 0.4), label="Stop-Loss %")

            with gr.Row():
                cfg_rsi_ob = gr.Slider(minimum=50, maximum=99, step=1, value=bot_config.get("rsi_overbought", 70), label="RSI Sobrecompra (> vender)")
                cfg_rsi_os = gr.Slider(minimum=1, maximum=50, step=1, value=bot_config.get("rsi_oversold", 30), label="RSI Sobreventa (< comprar)")

            with gr.Row():
                cfg_use_rsi = gr.Checkbox(label="Usar RSI en decisiones", value=bot_config.get("use_rsi", True))
                cfg_use_ema = gr.Checkbox(label="Usar EMA 20 en decisiones", value=bot_config.get("use_ema", True))
                cfg_use_boll = gr.Checkbox(label="Usar Bollinger en decisiones", value=bot_config.get("use_bollinger", True))
                
            with gr.Row():
                cfg_u_sch = gr.Checkbox(label="Restringir Horario Comercial (UTC)", value=bot_config.get("use_schedule", False))
                cfg_sch_start = gr.Textbox(label="Hora Inicio (HH:MM)", value=bot_config.get("schedule_start_utc", "08:00"))
                cfg_sch_end = gr.Textbox(label="Hora Fin (HH:MM)", value=bot_config.get("schedule_end_utc", "21:00"))
                
            btn_save_config = gr.Button("💾 Guardar Cambios en JSON", variant="primary")
            cfg_out = gr.Textbox(label="Estado del Guardado", interactive=False)
            
            btn_save_config.click(
                fn=save_settings,
                inputs=[cfg_symbol, cfg_interval, cfg_tp, cfg_sl, cfg_rsi_ob, cfg_rsi_os, cfg_use_rsi, cfg_use_ema, cfg_use_boll, cfg_u_sch, cfg_sch_start, cfg_sch_end],
                outputs=[cfg_out]
            )
            
        # ---------------------------------------------
        # PESTAÑA 5: WIDGET DE ESCRITORIO
        # ---------------------------------------------
        with gr.Tab("5. Widget Transparente"):
            gr.Markdown("### Control del Widget de Escritorio")
            with gr.Row():
                w_open = gr.Button("🟢 Abrir Widget Transparente", variant="primary")
                w_close = gr.Button("🔴 Cerrar Widget")
                w_status = gr.Textbox(label="Estado", interactive=False)
            
            w_open.click(fn=lambda: toggle_widget("Abrir"), inputs=[], outputs=[w_status])
            w_close.click(fn=lambda: toggle_widget("Cerrar"), inputs=[], outputs=[w_status])

if __name__ == "__main__":
    print("Iniciando GUI en http://127.0.0.1:7860")
    app.launch()
