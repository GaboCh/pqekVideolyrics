# main.py — Punto de entrada del proyecto
# Cambia el nombre del modulo y la clase segun tu proyecto
from app.gui.dashboard import create_dashboard
from app.utils.logger import setup_logger

logger = setup_logger("Main")

def main():
    logger.info("Iniciando el proyecto...")

    app = create_dashboard()

    logger.info("Lanzando interfaz en http://127.0.0.1:7860")
    app.launch(server_name="127.0.0.1", server_port=7860)

if __name__ == "__main__":
    main()
