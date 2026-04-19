import os
from groq import Groq
from app.utils.config import load_app_config
from app.utils.logger import logger

class LLMGenerator:
    def __init__(self):
        config = load_app_config()
        self.api_key = config.get("groq_api_key")
        if not self.api_key:
            logger.error("GROQ_API_KEY no encontrada en el .env")
            raise ValueError("GROQ_API_KEY missing")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile" # O el modelo disponible que soporte Groq

    def generate_html(self, prompt: str) -> str:
        """
        Llama a la API de Groq para obtener el HTML.
        """
        try:
            logger.info("Llamando a Groq para generar el video lírico...")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=6000, # Reducido a 6000 para no exceder los límites de la capa gratuita (TPM)
            )
            content = completion.choices[0].message.content
            
            # Limpiar posibles bloques de markdown
            if "```html" in content:
                content = content.split("```html")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            # Guardar copia de depuración
            with open("debug_output.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("HTML generado guardado localmente en debug_output.html (para depuración).")
                
            return content
        except Exception as e:
            logger.error(f"Error en LLMGenerator: {e}")
            return f"<h1>Error al generar el video</h1><p>{e}</p>"
