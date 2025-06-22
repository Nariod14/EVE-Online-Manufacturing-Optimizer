import logging
from app import create_app
from waitress import serve
import webbrowser
import sys

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)  # Add console output
    ]
)

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    try:
        host = '127.0.0.1'
        port = 5000
        url = f"http://{host}:{port}"
        
        logger.info("Starting EVE Online Manufacturing Optimizer")
        logger.info(f"Server is running at: {url}")
        logger.info("Opening web browser...")
        webbrowser.open(url)
        
        logger.info("Instructions:")
        logger.info("1. Use the web interface to manage blueprints and materials")
        logger.info("2. Click 'Optimize Production' to calculate the most profitable manufacturing plan")
        logger.info("3. Press Ctrl+C in this terminal to stop the server")
        
        serve(app, host=host, port=port)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:

        logger.info("Application shutting down")
        input("Press Enter to exit...")

from models import db
from flask_migrate import Migrate

migrate = Migrate(app, db)