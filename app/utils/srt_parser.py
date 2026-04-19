import re

def time_to_ms(time_str):
    """Convierte un timestamp SRT (ej. 00:01:23,450) a milisegundos."""
    parts = time_str.replace(',', ':').replace('.', ':').split(':')
    if len(parts) == 4:
        h, m, s, ms = parts
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    return 0

def parse_srt(file_path):
    """
    Lee un archivo SRT y devuelve un arreglo de diccionarios:
    [{"text": "Hola", "startMs": 1000, "endMs": 2500}, ...]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Cada bloque SRT está separado por doble salto de línea
    blocks = content.strip().split('\n\n')
    lyrics_data = []

    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # Línea 0 = ID del subtítulo
            # Línea 1 = Tiempos (ej. 00:00:10,500 --> 00:00:13,000)
            # Línea 2+ = Texto (puede usar más de una línea)
            timing = lines[1]
            text = " ".join(lines[2:]).strip()
            
            time_match = re.search(r'(\d+:\d+:\d+[.,]\d+)\s*-->\s*(\d+:\d+:\d+[.,]\d+)', timing)
            if time_match:
                start_ms = time_to_ms(time_match.group(1))
                end_ms = time_to_ms(time_match.group(2))
                lyrics_data.append({
                    "text": text,
                    "startMs": start_ms,
                    "endMs": end_ms
                })

    return lyrics_data

def get_srt_duration(file_path):
    """Retorna la duración total del SRT en segundos."""
    data = parse_srt(file_path)
    if not data: return 0
    return data[-1]['endMs'] / 1000.0
