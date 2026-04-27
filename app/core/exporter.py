import os
import subprocess
import asyncio
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

    @staticmethod
    async def convert_webm_to_mp4_async(webm_path, audio_path=None, output_path="fast_export.mp4"):
        """
        Convierte el archivo .webm de Playwright a .mp4 de forma ASÍNCRONA.
        Esto evita el error ConnectionResetError 10054 al no bloquear el event loop.
        """
        import time
        try:
            # Pequeña pausa para asegurar flush de Playwright
            await asyncio.sleep(2)

            if not os.path.exists(webm_path):
                logger.error(f"El archivo webm no existe: {webm_path}")
                return None

            if os.path.exists(output_path):
                try: os.remove(output_path)
                except: pass

            # Construir comando
            command = ['ffmpeg', '-y', '-i', webm_path]
            
            has_audio = audio_path and os.path.exists(audio_path)
            if has_audio:
                # Usamos quotes para rutas con caracteres especiales
                command.extend(['-i', audio_path])
                command.extend([
                    '-map', '0:v', '-map', '1:a', 
                    '-c:v', 'libx264', '-crf', '18', 
                    '-preset', 'veryfast', 
                    '-c:a', 'aac', '-shortest'
                ])
            else:
                command.extend(['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p'])

            command.append(output_path)

            logger.info(f"Iniciando conversión ASÍNCRONA: {' '.join(command)}")
            
            # Ejecutar FFmpeg sin bloquear el loop de asyncio
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg falló con código {process.returncode}")
                logger.error(stderr.decode())
                return None

            logger.info(f"Conversión finalizada: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error en convert_webm_to_mp4_async: {e}")
            return None
