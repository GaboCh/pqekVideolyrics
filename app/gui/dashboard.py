# app/gui/dashboard.py
# Interfaz principal con Gradio — adapta los tabs segun tu proyecto
import gradio as gr
import json
from app.core.client    import BinanceCoreClient
from app.core.strategies import run_strategy

def save_widget_config(symbols):
    try:
        with open("widget_config.json", "w", encoding="utf-8") as f:
            json.dump({"symbols": symbols}, f)
        return "Configuracion del widget guardada."
    except Exception as e:
        return f"Error: {e}"

def create_dashboard() -> gr.Blocks:
    client = BinanceCoreClient()

    with gr.Blocks(title="Mi Proyecto - Dashboard") as dashboard:
        gr.Markdown("# Mi Proyecto — Dashboard")
        gr.Markdown("Personaliza este dashboard segun tu proyecto.")

        # ── Tab 1: Conexion ────────────────────────────────────────────────
        with gr.Tab("Conexion API"):
            btn_check = gr.Button("Verificar Conexion")
            out_check = gr.Textbox(label="Estado", interactive=False)
            btn_check.click(fn=client.check_connection, outputs=[out_check])

        # ── Tab 2: Estrategia ──────────────────────────────────────────────
        with gr.Tab("Estrategia"):
            with gr.Row():
                dd_symbol   = gr.Dropdown(["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"],
                                          label="Par", value="BTCUSDT")
                dd_strategy = gr.Dropdown(["RSI","MACD","Grilla"],
                                          label="Estrategia", value="RSI")
            btn_run  = gr.Button("Ejecutar", variant="primary")
            out_logs = gr.Textbox(label="Log", lines=5, interactive=False)
            btn_run.click(fn=run_strategy, inputs=[dd_symbol, dd_strategy], outputs=[out_logs])

        # ── Tab 3: Widget ──────────────────────────────────────────────────
        with gr.Tab("Widget"):
            gr.Markdown("Monedas para el widget flotante de escritorio.")
            dd_syms = gr.Dropdown(
                choices=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"],
                value=["BTCUSDT","ETHUSDT"], multiselect=True,
                allow_custom_value=True, label="Monedas"
            )
            btn_save = gr.Button("Guardar", variant="primary")
            out_save = gr.Textbox(label="Estado", interactive=False)
            btn_save.click(fn=save_widget_config, inputs=[dd_syms], outputs=[out_save])

    return dashboard
