import os
import sys
import logging
import traceback
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from models import db
from flask_migrate import Migrate
from routes.materials import materials_bp
from routes.blueprints import blueprints_bp



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
    migrate = Migrate(flask_app, db)
    
    # with flask_app.app_context():
    #     try:
    #         db.create_all()
    #         logger.info("Database tables created successfully")
    #     except Exception as e:
    #         logger.error(f"Error creating database tables: {str(e)}")
    #         logger.error(traceback.format_exc())

    flask_app.register_blueprint(materials_bp)
    flask_app.register_blueprint(blueprints_bp)
    
    
    @flask_app.route('/')
    def index():
        return render_template('index.html')
    
    @flask_app.errorhandler(404)
    def not_found_error(error):
        logger.error(f"404 Not Found: {request.method} {request.path}")
        return jsonify({"error": "Not found"}), 404
    
    return flask_app
