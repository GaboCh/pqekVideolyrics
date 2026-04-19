import os
import time
import asyncio
from playwright.async_api import async_playwright
from app.utils.logger import logger

class Renderer:
    def __init__(self, output_dir="temp_frames"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def render_html(self, html_content: str, duration=30, fps=30, width=1920, height=1080):
        """
        Renderiza el HTML y captura los frames.
        """
        # Limpiar carpeta de frames previos
        for f in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, f))

        temp_html_path = os.path.abspath("temp_render.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(f"file://{temp_html_path}")
            
            # Esperar a que las librerías (GSAP/Three.js) carguen
            await page.wait_for_timeout(2000)

            # Congelar el tiempo y preparar para renderizado determinista
            await page.evaluate("window.IS_RENDERING = true;")
            
            total_frames = int(duration * fps)
            logger.info(f"Iniciando captura DETERMINISTA de {total_frames} frames ({width}x{height} a {fps}fps)...")

            for i in range(total_frames):
                # Calcular el tiempo exacto en ms para este frame
                current_ms = (i * 1000) / fps
                
                # Mover el "reloj" del HTML al milisegundo exacto
                await page.evaluate(f"window.seekTo({current_ms})")
                
                frame_path = os.path.join(self.output_dir, f"frame_{i:04d}.jpg")
                await page.screenshot(path=frame_path, type="jpeg", quality=85)
                
                if i % 30 == 0:
                    logger.info(f"Frame {i}/{total_frames} capturado ({int(current_ms/1000)}s)...")

            await browser.close()
            
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
            
        return self.output_dir
