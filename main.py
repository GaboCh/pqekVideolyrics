from app.gui.dashboard import launch_dashboard
from app.utils.logger import logger

def main():
    try:
        logger.info("Iniciando pqekVideolyrics...")
        launch_dashboard()
    except Exception as e:
        logger.critical(f"Error fatal al iniciar la aplicación: {e}")

if __name__ == "__main__":
    main()
