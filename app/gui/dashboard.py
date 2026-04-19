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
                            lyrics = gr.TextArea(label="Letra de la canción", placeholder="Pega aquí la letra...", lines=10)
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

                            gen_btn = gr.Button("✨ Generar", variant="primary", elem_id="gen-btn")
                            status_text = gr.Markdown("Listo para generar...")

                        with gr.Column(scale=1):
                            html_preview = gr.HTML(label="Preview", value="<div style='height:400px; display:flex; align-items:center; justify-content:center; background:#1a1a1e; border-radius:10px; color:#555;'>El preview aparecerá aquí</div>")
                            with gr.Accordion("Ver Código HTML (Depuración)", open=False):
                                raw_html_output = gr.Code(language="html", label="Código Fuente", interactive=False)

                    # Toggle visibility on mode change
                    def on_mode_change(mode):
                        is_template = "Template" in mode
                        return (
                            gr.update(visible=is_template),
                            gr.update(visible=not is_template),
                            gr.update(visible=not is_template)
                        )
                    use_template.change(fn=on_mode_change, inputs=[use_template], outputs=[template_choice, ai_style, model_choice])

                    def generate(lyr, sng, art, mode, tmpl, sty, mod):
                        import base64
                        self.llm.model = mod

                        if "Template" in mode:
                            # Map display name to key
                            template_map = {
                                "Space / Cosmos":           "Space / Cosmos",
                                "Neon Glow":                "Neon Glow",
                                "Grunge Brush (CSS)":       "Grunge Brush (CSS)",
                                "Zoom Punch (CSS)":         "Zoom Punch (CSS)",
                                "Pixel Retro — Mario (CSS)":"Pixel Retro (Mario)",
                                "🎵 Mix (Multi-estilo)":    "🎵 Mix (Multi-estilo)",
                            }
                            style_key = template_map.get(tmpl, tmpl)
                            html_code = PromptBuilder.get_template_html(lyr, sng, art, style_key)
                            source = f"⚡ Template: {tmpl}"
                            if not html_code:
                                return "<div style='color:orange;padding:20px'>Template no encontrado. Intenta con Groq.</div>", "❌ Template no encontrado", ""
                        else:
                            source = f"🤖 Groq ({mod})"
                            prompt = PromptBuilder.build_generation_prompt(lyr, sng, art, sty)
                            html_code = self.llm.generate_html(prompt)

                        self.current_html = html_code
                        b64_html = base64.b64encode(html_code.encode('utf-8')).decode('utf-8')
                        iframe = f'<iframe src="data:text/html;base64,{b64_html}" style="width:100%;height:500px;border:none;border-radius:10px;"></iframe>'
                        return iframe, f"HTML generado ✓ ({source})", html_code

                    gen_btn.click(
                        fn=generate,
                        inputs=[lyrics, song, artist, use_template, template_choice, ai_style, model_choice],
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
                            res = gr.Radio(["1920x1080", "1280x720", "1080x1920"], label="Resolución", value="1920x1080")
                            fps = gr.Slider(24, 60, step=6, label="FPS", value=30)
                            dur = gr.Slider(5, 60, step=5, label="Duración (segundos)", value=15)
                            
                            export_btn = gr.Button("🎥 Grabar y Exportar MP4", variant="primary")
                            
                        with gr.Column():
                            output_video = gr.Video(label="Video Final")
                    
                    async def export(resolution, frames_ps, duration):
                        if not self.current_html:
                            return None
                        
                        w, h = map(int, resolution.split('x'))
                        
                        # Renderizar frames
                        frames_dir = await self.renderer.render_html(self.current_html, duration=duration, fps=frames_ps, width=w, height=h)
                        
                        # Exportar a MP4
                        output_path = "output_video.mp4"
                        Exporter.frames_to_mp4(frames_dir, output_path, fps=frames_ps)
                        
                        return output_path

                    export_btn.click(fn=export, inputs=[res, fps, dur], outputs=[output_video])

        return demo

def launch_dashboard():
    dashboard = Dashboard()
    ui = dashboard.create_ui()
    # Pass CSS to launch method and open in browser to avoid silent startup
    ui.queue().launch(server_name="127.0.0.1", server_port=7860, inbrowser=True, css=dashboard.custom_css)
