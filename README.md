# Plantilla: Bot de Trading (Python + Gradio + Binance)

## Estructura del proyecto

```
Plantilla/
 instalar.bat         <- Instala el entorno (ejecutar primero)
 iniciar.bat          <- Arranca la aplicacion
 main.py              <- Punto de entrada
 requirements.txt     <- Dependencias Python
 .env                 <- Claves de API (NO subir a GitHub)
 app/
   bot_config.json    <- Parametros del bot (TP, SL, simbolo...)
   core/
     bot_logic.py     <- Motor de decision BUY/SELL/HOLD
     strategies.py    <- Estrategias de trading
     technical_analysis.py  <- Indicadores (RSI, EMA, Bollinger)
     chart_visualizer.py    <- Graficos Plotly interactivos
     data_fetcher.py        <- Descarga velas de Binance
     config_manager.py      <- Carga/guarda bot_config.json
     client.py              <- Conexion con la API
   gui/
     dashboard.py     <- Interfaz Gradio (pestanas)
     widget.py        <- Widget flotante de escritorio
   utils/
     config.py        <- Lee variables del .env
     logger.py        <- Sistema de logs
```

## Como usar esta plantilla

1. Copia esta carpeta con el nombre de tu nuevo proyecto
2. Edita `.env` con tus claves de Binance
3. Ejecuta `instalar.bat` (solo la primera vez o para reinstalar)
4. Ejecuta `iniciar.bat` para arrancar

## Personalizacion

| Archivo | Que cambiar |
|---|---|
| `app/core/bot_logic.py` | Condiciones de compra y venta |
| `app/core/strategies.py` | Nuevas estrategias |
| `app/bot_config.json` | Parametros por defecto (TP, SL, RSI...) |
| `app/gui/dashboard.py` | Pestanas e interfaz |
| `requirements.txt` | Agregar nuevas dependencias |
| `.env` | Tus claves reales de API |
