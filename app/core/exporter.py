import os
import subprocess
from app.utils.logger import logger

class Exporter:
    @staticmethod
    def frames_to_mp4(frames_dir, output_path="output.mp4", fps=30):
        """
        Convierte una secuencia de imágenes (frames) a un video MP4 usando FFmpeg.
        """
        try:
            # Comando de FFmpeg:
            # -framerate: fps de entrada
            # -i: patrón de archivos (frame_0000.png, etc)
            # -c:v: libx264 (H.264)
            # -pix_fmt: yuv420p para compatibilidad universal
            
            # Asegurarse de que el output no exista o sobreescribirlo
            if os.path.exists(output_path):
                os.remove(output_path)

            command = [
                'ffmpeg',
                '-y',
                '-framerate', str(fps),
                '-i', os.path.join(frames_dir, 'frame_%04d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', '18', # Calidad alta
                output_path
            ]
            
            logger.info(f"Ejecutando FFmpeg: {' '.join(command)}")
            
            # Ejecutar de forma síncrona para simplificar
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error en FFmpeg: {result.stderr}")
                return None
            
            logger.info(f"Video final exportado en: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error en Exporter: {e}")
            return None
