import os
import subprocess
from app.utils.logger import logger

class Exporter:
    @staticmethod
    def frames_to_mp4(frames_dir, output_path="output.mp4", fps=30, audio_path=None):
        """
        Convierte una secuencia de imágenes (frames) a un video MP4 usando FFmpeg,
        mezclando un archivo de audio opcionalmente.
        """
        try:
            if os.path.exists(output_path):
                os.remove(output_path)

            command = [
                'ffmpeg',
                '-y',
                '-framerate', str(fps),
                '-i', os.path.join(frames_dir, 'frame_%04d.jpg')
            ]
            
            # Si hay audio_path y el archivo existe, lo agregamos como otro input
            has_audio = audio_path and os.path.exists(audio_path)
            if has_audio:
                command.extend(['-i', audio_path])

            # Video codec - Optimización de velocidad
            command.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'superfast'])

            # Si hay audio, agregamos codec de audio
            if has_audio:
                command.extend(['-c:a', 'aac', '-shortest'])

            command.append(output_path)
            
            logger.info(f"Ejecutando FFmpeg: {' '.join(command)}")
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error en FFmpeg: {result.stderr}")
                return None
            
            logger.info(f"Video final exportado en: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error en Exporter: {e}")
            return None
