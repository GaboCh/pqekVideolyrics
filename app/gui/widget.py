import tkinter as tk
import requests
import threading
import time
import json
import os

class BinanceWidget:
    def __init__(self, root, symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"]):
        self.root = root
        self.symbols = symbols
        self.prices = {sym: "Cargando..." for sym in symbols}
        self.running = True
        
        self.setup_ui()
        
        # Iniciar hilo en segundo plano para actualizar precios sin bloquear la interfaz
        self.update_thread = threading.Thread(target=self.fetch_prices, daemon=True)
        self.update_thread.start()
        
        # Iniciar bucle de actualizacion de UI
        self.refresh_ui()

    def setup_ui(self):
        self.root.overrideredirect(True) # Quitar bordes de ventana de Windows
        self.root.attributes('-topmost', True) # Mantener siempre arriba
        self.root.attributes('-alpha', 0.8) # Transparencia (0.0 a 1.0)
        
        # Color de fondo oscuro estilo terminal/hacker
        self.bg_color = "#1E1E1E"
        self.fg_color = "#00FF00" # Verde neon para precios
        self.root.configure(bg=self.bg_color)
        
        # Frame principal para agrupar todo
        self.main_frame = tk.Frame(self.root, bg=self.bg_color, padx=10, pady=5)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Encabezado con boton para cerrar
        self.header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.header_frame.pack(fill=tk.X)
        
        self.title_lbl = tk.Label(self.header_frame, text="CRYPTO TRACKER", font=("Consolas", 10), bg=self.bg_color, fg="#AAAAAA")
        self.title_lbl.pack(side=tk.LEFT)
        
        self.close_btn = tk.Label(self.header_frame, text="[ X ]", font=("Consolas", 10, "bold"), fg="#FF5555", bg=self.bg_color, cursor="hand2")
        self.close_btn.pack(side=tk.RIGHT)
        self.close_btn.bind("<Button-1>", lambda e: self.close())
        
        # Labels individuales para cada simbolo
        self.labels = {}
        for sym in self.symbols:
            lbl = tk.Label(
                self.main_frame, 
                text=f"{sym}: --", 
                font=("Consolas", 12, "bold"), 
                bg=self.bg_color, 
                fg=self.fg_color
            )
            lbl.pack(anchor="w", pady=2)
            self.labels[sym] = lbl
            
        # Eventos para poder mover la ventana a cualquier lado con el raton pinchando y arrastrando
        self.main_frame.bind("<ButtonPress-1>", self.start_move)
        self.main_frame.bind("<B1-Motion>", self.do_move)
        
        self.header_frame.bind("<ButtonPress-1>", self.start_move)
        self.header_frame.bind("<B1-Motion>", self.do_move)

        self.title_lbl.bind("<ButtonPress-1>", self.start_move)
        self.title_lbl.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + event.x - self.x
        y = self.root.winfo_y() + event.y - self.y
        self.root.geometry(f"+{x}+{y}")

    def fetch_prices(self):
        while self.running:
            try:
                # Leer configuracion en tiempo real
                if os.path.exists("widget_config.json"):
                    with open("widget_config.json", "r", encoding="utf-8") as f:
                        config = json.load(f)
                        new_symbols = config.get("symbols", [])
                        if new_symbols and new_symbols != self.symbols:
                            self.symbols = new_symbols
                            # Inicializar nuevos valores
                            for s in self.symbols:
                                if s not in self.prices:
                                    self.prices[s] = "Cargando..."

                # Solo consultar a la API si hay simbolos
                if not self.symbols:
                    time.sleep(1)
                    continue

                # Consultar la API moneda por moneda para que un simbolo invalido no rompa los demas
                url_spot = 'https://api.binance.com/api/v3/ticker/price'
                url_futuros = 'https://fapi.binance.com/fapi/v1/ticker/price'
                
                for sym in self.symbols:
                    try:
                        resp = requests.get(url_spot, params={'symbol': sym}, timeout=3)
                        if resp.status_code == 200:
                            data = resp.json()
                            price = float(data['price'])
                            self.prices[sym] = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
                        else:
                            # Intentar buscarlo en Futuros si no existe en Spot
                            resp2 = requests.get(url_futuros, params={'symbol': sym}, timeout=3)
                            if resp2.status_code == 200:
                                data = resp2.json()
                                price = float(data['price'])
                                self.prices[sym] = f"${price:,.4f} (F)" if price < 1 else f"${price:,.2f} (F)"
                            else:
                                self.prices[sym] = "No listado"
                    except Exception:
                        self.prices[sym] = "Error de red"
            except Exception as e:
                pass
            
            # Duerme 3 segundos antes de volver a consultar para no saturar la API
            time.sleep(3)

    def refresh_ui(self):
        # Actualizar los labels con el valor mas reciente o recrearlos
        
        current_ui_symbols = list(self.labels.keys())
        if current_ui_symbols != self.symbols:
            # Recrear la interfaz entera si agregamos/quitamos monedas
            for lbl in self.labels.values():
                lbl.destroy()
            self.labels.clear()
            
            for sym in self.symbols:
                lbl = tk.Label(
                    self.main_frame, 
                    text=f"{sym}: --", 
                    font=("Consolas", 12, "bold"), 
                    bg=self.bg_color, 
                    fg=self.fg_color
                )
                lbl.pack(anchor="w", pady=2)
                self.labels[sym] = lbl

        # Refrescar los textos
        for sym in self.symbols:
            if sym in self.prices:
                text_to_show = f"{sym.replace('USDT', '')}: {self.prices[sym]}"
                self.labels[sym].config(text=text_to_show)
        
        # Programar la proxima actualizacion
        if self.running:
            self.root.after(1000, self.refresh_ui)

    def close(self):
        self.running = False
        self.root.destroy()
