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

            total_frames = duration * fps
            logger.info(f"Iniciando captura de {total_frames} frames ({width}x{height} a {fps}fps)...")

            for i in range(total_frames):
                frame_path = os.path.join(self.output_dir, f"frame_{i:04d}.png")
                await page.screenshot(path=frame_path)
                
                # Avanzar el tiempo si el HTML soporta control de tiempo manual o simplemente esperar
                # Como es una animación automática, capturamos en tiempo real con delays
                # NOTA: Para renderizado perfecto se usaría un sistema de 'seek' en la animación (ticker.sleep)
                # pero para este MVP capturaremos "live".
                await asyncio.sleep(1.0 / fps)
                
                if i % 30 == 0:
                    logger.info(f"Frame {i}/{total_frames} capturado...")

            await browser.close()
            
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
            
        return self.output_dir
