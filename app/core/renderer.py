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
            
    async def record_video_realtime(self, html_content: str, duration=30, width=1920, height=1080, selector="body"):
        """
        Graba el HTML en tiempo real con Audio Sintético Determinista.
        No depende de la tarjeta de sonido. Inyecta ondas matemáticas para el visualizador.
        """
        temp_html_path = os.path.abspath("temp_record.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        video_dir = os.path.abspath("temp_videos")
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)

        # Limpiar videos antiguos
        for f in os.listdir(video_dir):
            if f.endswith(".webm"):
                try: os.remove(os.path.join(video_dir, f))
                except: pass

        async with async_playwright() as p:
            # Volvemos a headless=True porque ya no necesitamos placa de sonido real
            logger.info("Iniciando grabación con motor de Audio Sintético...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--use-gl=desktop',
                    '--enable-webgl',
                    '--autoplay-policy=no-user-gesture-required',
                    '--hide-scrollbars'
                ]
            )
            
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=video_dir,
                record_video_size={"width": width, "height": height}
            )
            
            page = await context.new_page()
            await page.goto(f"file://{temp_html_path}")
            
            # Carga de assets
            await page.wait_for_timeout(3000) 

            # INYECCIÓN DEL MOTOR DE AUDIO SINTÉTICO Y SINCRONIZACIÓN
            logger.info("Hackeando motor de audio e iniciando Karaoke...")
            await page.evaluate("""
                () => {
                    // 1. Ocultar UI de edición
                    const uiIds = ['sync-panel', 'sync-toggle-btn', 'btn-restart', 'visual-selector'];
                    uiIds.forEach(id => {
                        const el = document.getElementById(id);
                        if(el) el.style.display = 'none';
                    });

                    // 2. INYECTAR AUDIO SINTÉTICO (Mock AnalyserNode)
                    // Esto engaña al código de Three.js y de las Barras 
                    // para que vean un ritmo constante aunque el navegador esté sordo.
                    window._freqData = new Uint8Array(128);
                    window._analyserNode = {
                        context: { state: 'running' },
                        frequencyBinCount: 128,
                        getByteFrequencyData: (arr) => {
                            const time = performance.now() / 1000;
                            // Creamos un pulso tipo "beat" (bajo)
                            const pulse = Math.pow(Math.sin(time * 3.8), 4); 
                            for(let i=0; i<arr.length; i++) {
                                if(i < 8) {
                                    // Graves (Barras iniciales y pulso galaxia)
                                    arr[i] = 160 + (95 * pulse);
                                } else if(i < 32) {
                                    // Medios (Vibración sutil)
                                    arr[i] = 80 + (40 * Math.sin(time * 5 + i*0.2));
                                } else {
                                    // Agudos (Ruido aleatorio)
                                    arr[i] = 20 + Math.random() * 30;
                                }
                            }
                        }
                    };

                    // 3. REINICIAR AUDIO REAL (Para el track de video)
                    const audio = document.getElementById('main-audio');
                    if(audio) {
                        audio.pause();
                        audio.currentTime = 0;
                        audio.muted = false;
                        audio.volume = 1.0;
                        audio.play().catch(e => console.log('Auto-play blocked, but synthetic audio will still move visuals.'));
                    }

                    // 4. REINICIAR KARAOKE (Sincronización Total)
                    if(typeof currentIdx !== 'undefined') currentIdx = 0;
                    if(typeof updateLines === 'function') updateLines();
                    if(typeof advance === 'function' && typeof LYRICS !== 'undefined') {
                        if(window._lyricsTimeout) clearTimeout(window._lyricsTimeout);
                        const firstDelay = (LYRICS[0] && LYRICS[0].startMs) ? LYRICS[0].startMs : 0;
                        window._lyricsTimeout = setTimeout(advance, firstDelay);
                    }

                    document.body.style.overflow = 'hidden';
                    document.body.style.backgroundColor = '#000';
                }
            """)

            # Un segundo de espera para que todo se asiente antes de los 30s de grabación
            await page.wait_for_timeout(1000)

            logger.info(f"Grabando video síntético durante {duration} segundos...")
            # El video se guarda al cerrar el contexto
            await asyncio.sleep(duration)
            video_path = await page.video.path()
            
            # Limpieza silenciosa para evitar WinError 10054 en Windows
            try:
                await page.close()
                await context.close()
                await browser.close()
            except:
                pass
            
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
            
        return video_path
