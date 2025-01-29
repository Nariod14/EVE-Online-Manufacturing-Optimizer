import os
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

flask_app = Flask(__name__)
CORS(flask_app)
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eve_optimizer.db'
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(flask_app)

def create_app():
    from routes import register_routes
    register_routes(flask_app)
    return flask_app
