import os
import sys
import logging
import traceback
from flask import Flask
from flask_cors import CORS
from models import db


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    from routes import register_routes
    
    flask_app = Flask(__name__)
    CORS(flask_app)
    
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        basedir = sys._MEIPASS
        instance_path = os.path.join(os.path.dirname(sys.executable), 'instances')
    else:
        # Running as script
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(basedir, 'instances')
    
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'eve_optimizer.db')

    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    db.init_app(flask_app)
    
    # with flask_app.app_context():
    #     try:
    #         db.create_all()
    #         logger.info("Database tables created successfully")
    #     except Exception as e:
    #         logger.error(f"Error creating database tables: {str(e)}")
    #         logger.error(traceback.format_exc())

    register_routes(flask_app)
    
    return flask_app
