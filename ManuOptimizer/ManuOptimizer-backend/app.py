import os
import sys
import logging
import traceback
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from models import db
from flask_migrate import Migrate
from routes.materials import materials_bp
from routes.blueprints import blueprints_bp
from routes.stations import stations_bp
from auth import auth_bp
from dotenv import load_dotenv
load_dotenv()


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
    if getattr(sys, 'frozen', False):
        # Compiled binary
        basedir = sys._MEIPASS
        instance_path = os.path.join(os.path.dirname(sys.executable), 'instances')
    else:
        # Running as script
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(basedir, 'instances')

    out_path = os.path.join(basedir, 'out')  # Moved here to always define

    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'eve_optimizer.db')

    # 👇 Serve frontend from `out/` as static folder
    flask_app = Flask(
        __name__,
        static_folder=out_path,
        static_url_path="/"
    )

    CORS(flask_app)
    flask_app.secret_key = os.getenv("FLASK_SECRET_KEY")
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    db.init_app(flask_app)
    Migrate(flask_app, db)

    flask_app.register_blueprint(materials_bp)
    flask_app.register_blueprint(blueprints_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(stations_bp)

    # 👇 This will serve index.html for all unknown routes (like a SPA)
    @flask_app.route("/")
    @flask_app.route("/<path:path>")
    def serve_frontend(path=""):
        if path != "" and os.path.exists(os.path.join(out_path, path)):
            return flask_app.send_static_file(path)
        return flask_app.send_static_file("index.html")

    @flask_app.errorhandler(404)
    def not_found_error(error):
        logger.error(f"404 Not Found: {request.method} {request.path}")
        return jsonify({"error": "Not found"}), 404

    return flask_app
