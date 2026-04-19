import gradio as gr
import os
import asyncio
from app.core.prompt_builder import PromptBuilder
from app.core.llm_generator import LLMGenerator
from app.core.renderer import Renderer
from app.core.exporter import Exporter
from app.utils.logger import logger

class Dashboard:
    def __init__(self):
        self.llm = LLMGenerator()
        self.renderer = Renderer()
        self.current_html = ""

    def create_ui(self):
        # Custom CSS para simular el look premium del mockup
        self.custom_css = """
        .gradio-container { background-color: #0d0d0f; color: #e8e8ed; font-family: 'Inter', sans-serif; }
        .tabs { border-bottom: 1px solid rgba(255,255,255,0.08); }
        .tab-item { padding: 14px 22px; font-weight: 500; }
        .btn-primary { background: #7c6af7 !important; border: none !important; box-shadow: 0 0 20px rgba(124,106,247,0.25); }
        .btn-primary:hover { background: #9b8cff !important; }
        .card { background: #141416; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 20px; }
        footer { display: none !important; }
        """

        with gr.Blocks(title="pqekVideolyrics") as demo:
            gr.Markdown("# 🎵 pqek<span>Video</span>lyrics", elem_classes=["logo"])
            
            with gr.Tabs() as tabs:
                
                # --- TAB 1: GENERAR ---
                with gr.Tab("1. Generar Lyric Video"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Accordion("📄 Letra (Texto o SRT)", open=True):
                                srt_upload = gr.File(label="Subir Archivo .srt (Sincronización Perfecta)", file_types=[".srt"])
                                lyrics = gr.TextArea(label="O pega aquí la letra (texto plano)", placeholder="Pega aquí la letra...\n(Si subes un SRT, esto se ignorará)", lines=5)
                            
                            with gr.Row():
                                song = gr.Textbox(label="Canción", placeholder="ej. Blinding Lights")
                                artist = gr.Textbox(label="Artista", placeholder="ej. The Weeknd")
                            
                            with gr.Row():
                                use_template = gr.Radio(
                                    choices=["⚡ Usar Template (instantáneo)", "🤖 Generar con IA (Groq)"],
                                    value="⚡ Usar Template (instantáneo)",
                                    label="Modo de Generación",
                                    elem_id="mode-radio"
                                )
                                preview_format = gr.Radio(
                                    choices=["Horizontal (16:9)", "Vertical TikTok (9:16)"],
                                    value="Horizontal (16:9)",
                                    label="Formato (Preview)",
                                    elem_id="format-radio"
                                )

                            template_choice = gr.Dropdown(
                                choices=[
                                    "Space / Cosmos",
                                    "Neon Glow",
                                    "Grunge Brush (CSS)",
                                    "Zoom Punch (CSS)",
                                    "Pixel Retro — Mario (CSS)",
                                    "Metal Slug (Arcade)",
                                    "Snow Globe (CSS)",
                                    "🎵 Mix (Multi-estilo)",
                                    "📸 Karaoke + Foto (Landscape)",
                                    "📸 Karaoke + Foto (Portrait)",
                                ],
                                label="🎨 Template Visual",
                                value="Space / Cosmos",
                                visible=True
                            )

                            ai_style = gr.Dropdown(
                                choices=[
                                    "Dark Cinematic",
                                    "Neon Glow (IA)",
                                    "Space / Cosmos (IA)",
                                    "Minimal White",
                                    "Fire & Smoke",
                                    "Ocean Wave",
                                    "Procedural CodePen (Kinematics/Math)",
                                ],
                                label="🤖 Estilo para IA",
                                value="Dark Cinematic",
                                visible=False
                            )

                            model_choice = gr.Dropdown(
                                choices=[
                                    "llama-3.3-70b-versatile",
                                    "openai/gpt-oss-120b",
                                    "openai/gpt-oss-20b",
                                    "qwen/qwen3-32b",
                                    "groq/compound",
                                    "llama-3.1-8b-instant"
                                ],
                                label="Modelo Lógica (Groq) — solo para modo IA",
                                value="openai/gpt-oss-20b",
                                visible=False
                            )

                            # Photo and Audio uploads
                            with gr.Row():
                                cover_image_upload = gr.Image(
                                    label="🖼️ Subir Portada",
                                    type="filepath",
                                    visible=False,
                                    elem_id="cover-upload"
                                )
                                audio_upload = gr.Audio(
                                    label="🎵 Subir Audio (MP3, WAV, etc.)",
                                    type="filepath"
                                )

                            gen_btn = gr.Button("✨ Generar", variant="primary", elem_id="gen-btn")
                            status_text = gr.Markdown("Listo para generar...")

                        with gr.Column(scale=1):
                            html_preview = gr.HTML(label="Preview con Audio", value="<div style='height:400px; display:flex; align-items:center; justify-content:center; background:#1a1a1e; border-radius:10px; color:#555;'>El preview aparecerá aquí.</div>")
                            with gr.Accordion("Ver Código HTML (Depuración)", open=False):
                                raw_html_output = gr.Code(language="html", label="Código Fuente", interactive=False)

                    # Toggle visibility on mode change
                    def on_mode_change(mode, template):
                        is_template = "Template" in mode
                        is_photo_template = is_template and "Karaoke + Foto" in template
                        return (
                            gr.update(visible=is_template),            # Template dropdown
                            gr.update(visible=not is_template),        # AI style dropdown
                            gr.update(visible=not is_template),        # Groq model
                            gr.update(visible=is_photo_template)       # Photo upload
                        )

                    def on_template_change(mode, template):
                        is_photo_template = ("Template" in mode) and ("Karaoke + Foto" in template)
                        return gr.update(visible=is_photo_template)

                    use_template.change(fn=on_mode_change, inputs=[use_template, template_choice], outputs=[template_choice, ai_style, model_choice, cover_image_upload])
                    template_choice.change(fn=on_template_change, inputs=[use_template, template_choice], outputs=[cover_image_upload])

                    def generate(srt_file, lyr, sng, art, mode, tmpl, sty, mod, cover_img_path, format_ratio, audio_path):
                        import base64
                        import json
                        from app.utils.srt_parser import parse_srt
                        
                        self.llm.model = mod

                        # Usar SRT si está disponible
                        final_lyrics = lyr
                        if srt_file:
                            srt_data = parse_srt(srt_file.name)
                            final_lyrics = json.dumps(srt_data, ensure_ascii=False)

                        if "Template" in mode:
                            # Map display name to key
                            template_map = {
                                "Space / Cosmos":           "Space / Cosmos",
                                "Neon Glow":                "Neon Glow",
                                "Grunge Brush (CSS)":       "Grunge Brush (CSS)",
                                "Zoom Punch (CSS)":         "Zoom Punch (CSS)",
                                "Pixel Retro — Mario (CSS)":"Pixel Retro (Mario)",
                                "Metal Slug (Arcade)":      "Metal Slug (Arcade)",
                                "Snow Globe (CSS)":         "Snow Globe (CSS)",
                                "🎵 Mix (Multi-estilo)":    "🎵 Mix (Multi-estilo)",
                                "📸 Karaoke + Foto (Landscape)": "📸 Karaoke + Foto (Landscape)",
                                "📸 Karaoke + Foto (Portrait)": "📸 Karaoke + Foto (Portrait)",
                            }
                            style_key = template_map.get(tmpl, tmpl)
                            html_code = PromptBuilder.get_template_html(final_lyrics, sng, art, style_key, cover_image_path=cover_img_path, audio_path=audio_path)
                            source = f"⚡ Template: {tmpl}"
                            if not html_code:
                                return "<div style='color:orange;padding:20px'>Template no encontrado. Intenta con Groq.</div>", "❌ Template no encontrado", ""
                        else:
                            source = f"🤖 Groq ({mod})"
                            prompt = PromptBuilder.build_generation_prompt(final_lyrics, sng, art, sty)
                            html_code = self.llm.generate_html(prompt)

                        self.current_html = html_code
                        
                        import html
                        escaped_html = html.escape(html_code)
                        
                        iframe_style = "width:100%;height:500px;border:none;border-radius:10px;"
                        if format_ratio == "Vertical TikTok (9:16)":
                            # Centramos el iframe y le damos proporción de celular (aprox 360x640)
                            iframe_style = "width:360px;height:640px;border:2px solid #333;border-radius:16px;box-shadow: 0 10px 30px rgba(0,0,0,0.5);margin: 0 auto;display:block;"

                        iframe = f'<iframe srcdoc="{escaped_html}" style="{iframe_style}" allow="autoplay"></iframe>'

                        return iframe, f"HTML generado ✓ ({source})", html_code

                    gen_btn.click(
                        fn=generate,
                        inputs=[srt_upload, lyrics, song, artist, use_template, template_choice, ai_style, model_choice, cover_image_upload, preview_format, audio_upload],
                        outputs=[html_preview, status_text, raw_html_output]
                    )


                # --- TAB 2: AJUSTAR ---
                with gr.Tab("2. Ajustar Estilo"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### Refinar con IA")
                            adj_prompt = gr.TextArea(label="Dile a Groq qué cambiar", placeholder="ej. pon el fondo rojo y haz que las letras brillen más...", lines=5)
                            adj_btn = gr.Button("🔄 Aplicar cambios", variant="primary")
                            
                            gr.Examples(
                                examples=["letras blancas", "partículas doradas", "efecto typewriter", "fondo degradado"],
                                inputs=adj_prompt,
                                label="Sugerencias rápidas"
                            )

                        with gr.Column(scale=1):
                            html_preview_adj = gr.HTML(label="Preview Actualizado")

                    def adjust(p):
                        if not self.current_html:
                            return "<div style='color:red'>Primero genera un video en la pestaña 1</div>"
                        prompt = PromptBuilder.build_adjustment_prompt(self.current_html, p)
                        html_code = self.llm.generate_html(prompt)
                        self.current_html = html_code
                        
                        import base64
                        b64_html = base64.b64encode(html_code.encode('utf-8')).decode('utf-8')
                        iframe_preview = f'<iframe src="data:text/html;base64,{b64_html}" style="width: 100%; height: 500px; border: none; border-radius: 10px; background: #ffffff;"></iframe>'
                        
                        return iframe_preview

                    adj_btn.click(fn=adjust, inputs=[adj_prompt], outputs=[html_preview_adj])

                # --- TAB 3: EXPORTAR ---
                with gr.Tab("3. Exportar MP4"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### ⚙️ Configuración de Exportación")
                            
                            platform = gr.Radio(
                                ["📺 YouTube (Horizontal)", "📱 TikTok / Reels (Vertical)"], 
                                label="Plataforma de destino", 
                                value="📱 TikTok / Reels (Vertical)"
                            )
                            
                            quality = gr.Radio(
                                ["🚀 Borrador (Rápido)", "✅ Normal (HD)", "💎 Full HD (Lento)"], 
                                label="Calidad de salida", 
                                value="✅ Normal (HD)"
                            )

                            info_display = gr.Markdown("### ℹ️ Información de Archivos\n*Sube un audio o SRT para ver su duración.*")
                            
                            export_btn = gr.Button("🎬 Grabar y Exportar MP4", variant="primary")

                        with gr.Column():
                            output_video = gr.Video(label="Video Final")
                    
                    def get_audio_duration(file_path):
                        if not file_path: return None
                        try:
                            import subprocess
                            cmd = [
                                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=noprint_wrappers=1:nokey=1", file_path
                            ]
                            result = subprocess.run(cmd, capture_output=True, text=True)
                            dur_val = float(result.stdout.strip())
                            return dur_val
                        except:
                            return None

                    def update_info(srt_f, audio_f):
                        from app.utils.srt_parser import get_srt_duration
                        msg = "### ℹ️ Información de Archivos\n"
                        final_dur = 30
                        
                        if srt_f:
                            s_dur = get_srt_duration(srt_f.name)
                            msg += f"✅ **SRT:** {int(s_dur//60)}:{int(s_dur%60):02d}s\n"
                            final_dur = s_dur
                        
                        if audio_f:
                            a_dur = get_audio_duration(audio_f)
                            if a_dur:
                                msg += f"🎵 **Audio:** {int(a_dur//60)}:{int(a_dur%60):02d}s\n"
                                final_dur = a_dur
                        
                        if not srt_f and not audio_f:
                            msg += "*No se han detectado archivos.*"
                        else:
                            msg += f"\n> [!TIP]\n> Se grabarán **{final_dur:.1f} segundos** automáticamente."
                            
                        return msg

                    # Al subir archivos actualizamos la info. Nota: ya no movemos slider porque lo quitamos
                    srt_upload.change(fn=update_info, inputs=[srt_upload, audio_upload], outputs=[info_display])
                    audio_upload.change(fn=update_info, inputs=[srt_upload, audio_upload], outputs=[info_display])

                    async def export_vid(plat, qual, audio_file):
                        if not self.current_html:
                            return None
                        
                        # Mapeo de presets
                        is_vertical = "TikTok" in plat
                        
                        # Resoluciones base
                        if qual == "🚀 Borrador (Rápido)":
                            w, h, fps = (640, 360, 24) if not is_vertical else (360, 640, 24)
                        elif qual == "💎 Full HD (Lento)":
                            w, h, fps = (1920, 1080, 30) if not is_vertical else (1080, 1920, 30)
                        else: # Normal
                            w, h, fps = (1280, 720, 30) if not is_vertical else (720, 1280, 30)

                        audio_dur = get_audio_duration(audio_file)
                        final_duration = audio_dur if audio_dur else 30
                        
                        logger.info(f"Exportando para {plat} en calidad {qual}. Total: {final_duration}s")

                        # Renderizar
                        frames_dir = await self.renderer.render_html(self.current_html, duration=final_duration, fps=fps, width=w, height=h)
                        
                        # Mezclar
                        output_path = "output_video.mp4"
                        Exporter.frames_to_mp4(frames_dir, output_path, fps=fps, audio_path=audio_file)
                        
                        return output_path

                    export_btn.click(fn=export_vid, inputs=[platform, quality, audio_upload], outputs=[output_video])

        return demo

def launch_dashboard():
    dashboard = Dashboard()
    ui = dashboard.create_ui()
    # Pass CSS to launch method and open in browser to avoid silent startup
    ui.queue().launch(server_name="127.0.0.1", server_port=7860, inbrowser=True, css=dashboard.custom_css)
