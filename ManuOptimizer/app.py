# app.py
import os
import logging
import traceback
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from models import db, Blueprint, Material
from pulp import PULP_CBC_CMD, LpProblem, LpVariable, lpSum, value, LpMaximize, LpStatus


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Outputs to console
        logging.FileHandler('app.log', mode='w')  # Writes to log file, overwriting previous logs
    ]
)
logger = logging.getLogger(__name__)


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
            name = data['name']
            materials = data['materials']
            sell_price = data['sell_price']
            material_cost = data['material_cost']

            existing_blueprint = Blueprint.query.filter_by(name=name).first()
            if existing_blueprint:
                existing_blueprint.materials = materials
                existing_blueprint.sell_price = sell_price
                existing_blueprint.material_cost = material_cost
                db.session.commit()
                return jsonify({"message": "Blueprint updated successfully"}), 200

            new_blueprint = Blueprint(name=name, materials=materials, sell_price=sell_price, material_cost=material_cost)
            db.session.add(new_blueprint)
            db.session.commit()
            return jsonify({"message": "Blueprint added successfully"}), 201

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding blueprint: {str(e)}")
            return jsonify({"error": "An error occurred while adding the blueprint"}), 500

    @flask_app.route('/blueprint/<int:id>', methods=['GET'])
    def get_blueprint(id):
        blueprint = Blueprint.query.get_or_404(id)
        return jsonify({
            'id': blueprint.id,
            'name': blueprint.name,
            'materials': blueprint.materials,
            'sell_price': blueprint.sell_price
        })

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
        blueprint = Blueprint.query.get_or_404(id)
        data = request.json
        blueprint.name = data.get('name', blueprint.name)
        blueprint.materials = data.get('materials', blueprint.materials)
        blueprint.sell_price = data.get('sell_price', blueprint.sell_price)
        blueprint.max = data.get('max', blueprint.max)
        db.session.commit()
        return jsonify({'message': 'Blueprint updated successfully'})
    
    @flask_app.route('/blueprints/reset_max', methods=['POST'])
    def reset_all_blueprint_max():
        try:
            blueprints = Blueprint.query.all()
            for blueprint in blueprints:
                blueprint.max = None  # Set max to None
            db.session.commit()
            return jsonify({"message": "All blueprint max values have been reset."}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting all blueprint max values: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": "An error occurred while resetting max values."}), 500


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
            blueprints = Blueprint.query.all()
            materials = Material.query.all()

            prob = LpProblem("Modules Optimization", LpMaximize)

            x = {b.name: LpVariable(f"x_{b.name}", lowBound=0, cat='Integer') for b in blueprints}

            prob += lpSum((b.sell_price - b.material_cost) * x[b.name] for b in blueprints)

            for m in materials:
                prob += lpSum(b.materials.get(m.name, 0) * x[b.name] for b in blueprints) <= m.quantity

            for b in blueprints:
                if b.max is not None:
                    prob += x[b.name] <= b.max

            prob.solve(PULP_CBC_CMD())

            if LpStatus[prob.status] == 'Optimal':
                results = {
                    "status": "Optimal",
                    "total_profit": sum(b.sell_price * value(x[b.name]) for b in blueprints),
                    "what_to_produce": {b.name: value(x[b.name]) for b in blueprints},
                    "material_usage": {
                        m.name: {
                            "used": sum(b.materials.get(m.name, 0) * value(x[b.name]) for b in blueprints),
                            "remaining": m.quantity - sum(b.materials.get(m.name, 0) * value(x[b.name]) for b in blueprints)
                        } for m in materials
                    },
                    "true_profit": sum((b.sell_price - b.material_cost) * value(x[b.name]) for b in blueprints)
                }

                return jsonify(results), 200
            else:
                return jsonify({"status": "No optimal solution found"}), 400

        except Exception as e:
            app.logger.error("An error occurred during optimization: %s", str(e))
            return jsonify({"error": "An error occurred during optimization"}), 500


    return flask_app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=False)
