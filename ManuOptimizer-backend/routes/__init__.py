from . import blueprints
from . import materials


def register_routes(app):
    app.register_blueprint(blueprints.blueprints)
    app.register_blueprint(materials.materials)