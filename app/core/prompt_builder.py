import os
import json


# Template folder — pre-made HTML templates that look great
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates")

STYLE_TO_TEMPLATE = {
    "Space / Cosmos":        "space_cosmos.html",
    "Neon Glow":             "neon_glow.html",
    "Grunge Brush (CSS)":    "grunge_brush.html",
    "Zoom Punch (CSS)":      "zoom_punch.html",
    "Pixel Retro (Mario)":   "pixel_retro.html",
    "Metal Slug (Arcade)":   "metal_slug.html",
    "Snow Globe (CSS)":      "snow_globe.html",
    "🎵 Mix (Multi-estilo)": "mix_template.html",
}



class PromptBuilder:

    @staticmethod
    def fill_template(template_path: str, song_name: str, artist_name: str, lyrics: str) -> str | None:
        """
        Fill a pre-made HTML template with song data.
        """
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                html = f.read()

            lines = lyrics.split("\n")
            lyrics_array_content = ", ".join(json.dumps(l, ensure_ascii=False) for l in lines)

            html = html.replace("{{SONG_NAME}}", song_name or "Lyric Video")
            html = html.replace("{{ARTIST_NAME}}", artist_name or "")
            html = html.replace("{{LYRICS_JSON}}", lyrics_array_content)
            html = html.replace("{{FIRST_LINE}}", lines[0] if lines else "")
            return html
        except Exception as e:
            return None

    @staticmethod
    def get_template_html(lyrics: str, song_name: str, artist_name: str, style_name: str) -> str | None:
        """
        Try to find and fill a template for the given style.
        Returns filled HTML or None if no template exists for this style.
        """
        # Special handling for Mix mode: auto-tag lines by section
        if style_name == "\U0001f3b5 Mix (Multi-estilo)":
            tagged_lyrics = PromptBuilder._tag_lyrics_for_mix(lyrics)
            template_path = os.path.join(TEMPLATES_DIR, "mix_template.html")
            return PromptBuilder.fill_template(template_path, song_name, artist_name, tagged_lyrics)

        template_file = STYLE_TO_TEMPLATE.get(style_name)
        if not template_file:
            return None
        template_path = os.path.join(TEMPLATES_DIR, template_file)
        return PromptBuilder.fill_template(template_path, song_name, artist_name, lyrics)

    @staticmethod
    def _tag_lyrics_for_mix(lyrics: str) -> str:
        """
        Auto-tag lyric sections alternating between GALAXY (verse), NEON (chorus/repeated), GRUNGE (bridge).
        Empty lines delimit sections.
        """
        sections = []
        current = []
        for line in lyrics.split("\n"):
            if line.strip() == "":
                sections.append(current)
                current = []
            else:
                current.append(line)
        if current:
            sections.append(current)

        themes = ["GALAXY", "NEON", "GALAXY", "NEON", "GRUNGE", "GALAXY", "NEON"]
        tagged_lines = []
        for i, section in enumerate(sections):
            theme = themes[i % len(themes)]
            for line in section:
                tagged_lines.append(f"{theme}:{line}")
            tagged_lines.append("")  # blank between sections
        return "\n".join(tagged_lines)

    @staticmethod
    def build_generation_prompt(lyrics: str, song_name: str, artist_name: str, style_name: str) -> str:
        """
        Construye el prompt para Groq (usado cuando no existe un template para el estilo).
        """
        styles = {
            "Dark Cinematic": "deep black/indigo, subtle gold particles, slow cinematic camera drift, dramatic shadows.",
            "Neon Glow": "electric cyan #00ffff and hot pink #ff0080, fast pulsing lights, glitch text effect.",
            "Space / Cosmos": "deep navy + nebula purple, star trails, slow galaxy rotation.",
            "Minimal White": "clean white background, black text, single geometric ring, smooth opacity transitions.",
            "Fire & Smoke": "warm oranges and reds, upward-moving particle drift, flickering point light.",
            "Ocean Wave": "teal/aqua palette, sine-wave animated plane geometry, flowing particles.",
            "Procedural CodePen (Kinematics/Math)": "black bg, white wireframe geometry, physics-based particle chains."
        }
        selected_style = styles.get(style_name, "dark cinematic, professional.")

        prompt = f"""
You are a world-class Creative Coder and WebGL artist (Shadertoy, Codrops, Awwwards SOTD level).
Create a STUNNING animated lyric video in ONE standalone HTML file. No markdown. No explanations. Start with <!DOCTYPE html>.

SONG INFO:
- Title: {song_name}
- Artist: {artist_name}
- Style: {style_name} — {selected_style}
- Lyrics (one per line): {lyrics}

MANDATORY LIBRARIES in <head>:
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&display=swap" rel="stylesheet">

THREE.JS REQUIREMENTS:
1. Generate a circular disc texture using a Canvas 2D radial gradient so particles render as CIRCLES (not squares):
   const disc = (() => {{ const c = document.createElement('canvas'); c.width=64; c.height=64; const cx = c.getContext('2d'); const g = cx.createRadialGradient(32,32,0,32,32,32); g.addColorStop(0,'rgba(255,255,255,1)'); g.addColorStop(1,'rgba(255,255,255,0)'); cx.fillStyle=g; cx.beginPath(); cx.arc(32,32,32,0,Math.PI*2); cx.fill(); return new THREE.CanvasTexture(c); }})();
2. Use this disc as `map` in PointsMaterial with `alphaTest: 0.001, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true`.
3. Build a 8000+ particle galaxy using BufferGeometry with spiral arms. Slow rotation in animate loop.
4. Add a glowing RingGeometry with GSAP breathing pulse.

LYRICS DISPLAY (GSAP):
- ONE line at a time, centered, `position:absolute`, font-size `clamp(1.8rem,5vw,5rem)`.
- Each line: fromTo(opacity 0→1, blur 16px→0, y 40→0, duration 0.65), visible 2.3s, then to(opacity→0, y→-28, blur→8px, 0.45s).
- Show song title + artist for 3s before lyrics start.
- style colors: {selected_style}
OUTPUT: raw HTML only, starting with <!DOCTYPE html>.
        """
        return prompt

    @staticmethod
    def build_adjustment_prompt(current_html: str, adjustment_text: str) -> str:
        prompt = f"""
I have a lyric video HTML. Apply these changes: {adjustment_text}

Keep all Three.js and GSAP logic intact. Return the complete updated HTML starting with <!DOCTYPE html>. No markdown.

Current HTML:
{current_html}
        """
        return prompt
