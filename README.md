# pqekVideolyrics — AI Lyric Video Generator

> Pega la letra de una cancion → Groq LLM genera un HTML animado estilo lyric video profesional → preview en iframe → exporta como MP4.

## Stack tecnologico

| Componente | Tecnologia |
|---|---|
| Interfaz | Python + Gradio |
| LLM | Groq API (llama-3.3-70b) |
| Animaciones generadas | GSAP, Three.js, CSS |
| Renderizado headless | Playwright |
| Exportacion video | FFmpeg |

## Estructura del proyecto

```
pqekVideolyrics/
  instalar.bat         <- Instala el entorno (ejecutar primero)
  iniciar.bat          <- Arranca la aplicacion
  main.py              <- Punto de entrada
  requirements.txt     <- Dependencias Python
  .env                 <- Claves de API (NO subir a GitHub)
  app/
    core/
      llm_generator.py   <- Llama a Groq y genera el HTML animado
      renderer.py        <- Playwright: abre el HTML headless y graba frames
      exporter.py        <- FFmpeg: convierte frames a MP4
      prompt_builder.py  <- Construye el prompt para Groq segun la letra
    gui/
      dashboard.py       <- Interfaz Gradio con las 3 pestanas
    utils/
      config.py          <- Lee variables del .env
      logger.py          <- Sistema de logs
```

## Pestanas de la interfaz

### 1. Letra + Generar
- Input de texto con la letra de la cancion
- Boton "Generar Video" → llama a Groq
- Groq devuelve un HTML completo con animaciones (GSAP / Three.js / CSS)
- Preview del resultado en un `<iframe>` embebido

### 2. Ajustar Estilo
- Campo de prompt adicional (ej: "fondo negro con particulas doradas")
- Groq regenera el HTML aplicando los cambios de estilo
- Preview actualizado en tiempo real

### 3. Exportar MP4
- Selector de resolucion (720p / 1080p / 4K)
- Selector de FPS (24 / 30 / 60)
- Duracion en segundos
- Playwright graba el HTML animado frame a frame
- FFmpeg ensambla el MP4 y lo ofrece para descarga

## Como usar esta plantilla

1. Copia esta carpeta con el nombre de tu nuevo proyecto
2. Crea tu archivo `.env` con tu clave de Groq:
   ```
   GROQ_API_KEY=gsk_xxxxxxxxxxxx
   ```
3. Ejecuta `instalar.bat` (solo la primera vez)
4. Ejecuta `iniciar.bat` para arrancar la app en `http://127.0.0.1:7860`

## Personalizacion

| Archivo | Que cambiar |
|---|---|
| `app/core/prompt_builder.py` | El prompt que le das a Groq (estilo, efectos, librerias) |
| `app/core/llm_generator.py` | Modelo de Groq, temperatura, max_tokens |
| `app/core/renderer.py` | Resolucion del viewport de Playwright, delay entre frames |
| `app/core/exporter.py` | Codec, bitrate, formato de salida (MP4, WebM) |
| `app/gui/dashboard.py` | Pestanas, controles y layout de Gradio |
| `requirements.txt` | Agregar nuevas dependencias |

## Dependencias principales

```bash
pip install gradio groq playwright
playwright install chromium
```

FFmpeg debe estar instalado en el sistema y disponible en el PATH.
