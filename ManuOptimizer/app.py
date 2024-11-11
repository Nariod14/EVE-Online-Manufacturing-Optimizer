# pylint: disable=no-else-return
# trunk-ignore-all(isort)
# pylint: disable=missing-class-docstring
"""Implementation of the blueprint optimizer using the PuLP library."""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models import db, Blueprint, Material
from pulp import PULP_CBC_CMD, LpProblem, LpVariable, lpSum, value, LpMaximize, LpStatus

def create_app():
    flask_app = Flask(__name__)
    CORS(flask_app)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eve_optimizer.db'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(flask_app)

    @flask_app.route('/')
    def index():
        return render_template('index.html')
    @flask_app.route('/blueprint', methods=['POST'])
    def add_blueprint():
        try:
            data = request.json
            if not all(key in data for key in ['name', 'materials', 'sell_price']):
                return jsonify({"error": "Missing required fields"}), 400
            new_blueprint = Blueprint(name=data['name'], materials=data['materials'], sell_price=data['sell_price'])
            db.session.add(new_blueprint)
            db.session.commit()
            return jsonify({"message": "Blueprint added successfully"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @flask_app.route('/blueprint', methods=['GET'])
    def get_blueprints():
        blueprints = Blueprint.query.all()
        return jsonify([
            {"id": b.id, "name": b.name, "materials": b.materials, "sell_price": b.sell_price}
            for b in blueprints
        ]), 200

    @flask_app.route('/material', methods=['POST'])
    def add_material():
        data = request.json
        material = Material.query.filter_by(name=data['name']).first()
        if material:
            material.quantity = data['quantity']
        else:
            new_material = Material(name=data['name'], quantity=data['quantity'])
            db.session.add(new_material)
        db.session.commit()
        return jsonify({"message": "Material updated successfully"}), 200

    @flask_app.route('/material', methods=['GET'])
    def get_materials():
        materials = Material.query.all()
        return jsonify([
            {"id": m.id, "name": m.name, "quantity": m.quantity}
            for m in materials
        ]), 200
        
    @flask_app.route('/blueprint/<int:id>', methods=['PUT'])
    def update_blueprint(id):
        data = request.json
        blueprint = Blueprint.query.get_or_404(id)
        blueprint.name = data.get('name', blueprint.name)
        blueprint.sell_price = data.get('sell_price', blueprint.sell_price)
        db.session.commit()
        return jsonify({"message": "Blueprint updated successfully"}), 200

    @flask_app.route('/blueprint/<int:id>', methods=['DELETE'])
    def delete_blueprint(id):
        blueprint = Blueprint.query.get_or_404(id)
        db.session.delete(blueprint)
        db.session.commit()
        return jsonify({"message": "Blueprint deleted successfully"}), 200

    @flask_app.route('/material/<int:id>', methods=['PUT'])
    def update_material(id):
        data = request.json
        material = Material.query.get_or_404(id)
        material.quantity = data.get('quantity', material.quantity)
        db.session.commit()
        return jsonify({"message": "Material updated successfully"}), 200

    @flask_app.route('/material/<int:id>', methods=['DELETE'])
    def delete_material(id):
        material = Material.query.get_or_404(id)
        db.session.delete(material)
        db.session.commit()
        return jsonify({"message": "Material deleted successfully"}), 200

    @flask_app.route('/optimize', methods=['GET'])
    def optimize():
        try:
            # Fetch all blueprints and materials from the database
            blueprints = Blueprint.query.all()
            materials = Material.query.all()

            # Create the LP problem
            prob = LpProblem("Modules Optimization", LpMaximize)

            # Define decision variables
            x = {b.name: LpVariable(f"x_{b.name}", lowBound=0, cat='Integer') for b in blueprints}

            # Set the objective function
            prob += lpSum(b.sell_price * x[b.name] for b in blueprints)

            # Add the material constraints
            for m in materials:
                prob += lpSum(b.materials.get(m.name, 0) * x[b.name] for b in blueprints) <= m.quantity

            # Solve the problem using CBC solver
            prob.solve(PULP_CBC_CMD())

            if LpStatus[prob.status] == 'Optimal':
                results = {
                    "status": "Optimal",
                    "total_profit": value(prob.objective),
                    "what to produce": {b.name: value(x[b.name]) for b in blueprints},
                    "material_usage": {}
                }

                # Calculate material usage
                for m in materials:
                    usage = sum(b.materials.get(m.name, 0) * value(x[b.name]) for b in blueprints)
                    results["material_usage"][m.name] = {
                        "used": usage,
                        "remaining": m.quantity - usage
                    }

                return jsonify(results), 200
            else:
                return jsonify({"status": "No optimal solution found"}), 400

        except Exception as e:
            flask_app.logger.error("An error occurred during optimization: %s", str(e))
            return jsonify({"error": "An error occurred during optimization"}), 500

    return flask_app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)  # Set to False for production