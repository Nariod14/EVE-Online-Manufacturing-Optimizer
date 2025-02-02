import os
import subprocess
import sys
from flask import jsonify, render_template, request
import logging
import traceback

import pulp
from models import db, Blueprint, Material
from pulp import LpProblem, LpVariable, lpSum, value, LpMaximize, LpStatus, PULP_CBC_CMD

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')
    @app.route('/blueprint', methods=['POST'])
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
            logger.info("Blueprint added successfully")
            return jsonify({"message": "Blueprint added successfully"}), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding blueprint! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while adding the blueprint"}), 500

    @app.route('/blueprint/<int:id>', methods=['GET'])
    def get_blueprint(id):
        try:
            blueprint = Blueprint.query.get_or_404(id)
            return jsonify({
                'id': blueprint.id,
                'name': blueprint.name,
                'materials': blueprint.materials,
                'sell_price': blueprint.sell_price    
            }), 200
        except Exception as e:
            logger.error(f"Error getting blueprint! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'An error occurred while getting the blueprint'
            }), 500
    

    @app.route('/blueprint', methods=['GET'])
    def get_blueprints():
        try:
            blueprints = Blueprint.query.all()
            logger.info("Blueprints retrieved successfully")
            return jsonify([
                {"id": b.id, "name": b.name, "materials": b.materials, "sell_price": b.sell_price}
                for b in blueprints
            ]), 200
        except Exception as e:
            logger.error(f"Error getting blueprints! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while getting the blueprints"}), 500

    @app.route('/material', methods=['POST'])
    def add_material():
        try:
            data = request.json
            logger.info(f"Received material data: {data}")
            
            material = Material.query.filter_by(name=data['name']).first()
            if material:
                logger.info(f"Updating existing material: {data['name']}")
                material.quantity = data['quantity']
            else:
                logger.info(f"Adding new material: {data['name']}")
                new_material = Material(name=data['name'], quantity=data['quantity'])
                db.session.add(new_material)
            
            db.session.commit()
            logger.info("Material added/updated successfully")
            return jsonify({"message": "Material updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding/updating material: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": "An error occurred while adding/updating the material"}), 500
    
    @app.route('/update_materials', methods=['POST'])
    def update_materials():
        try:
            data = request.json
            materials = data.get('materials', {})
            update_type = data.get('updateType', 'replace')

            logger.info(f"Received materials data: {materials}")
            logger.info(f"Update type: {update_type}")

            if update_type == 'replace':
                # Clear all existing materials before adding new ones
                Material.query.delete()
                db.session.commit()
                logger.info("All existing materials have been deleted.")

            for name, quantity in materials.items():
                material = Material.query.filter_by(name=name).first()
                if material:
                    if update_type == 'add':
                        logger.info(f"Adding to existing material: {name}, current quantity: {material.quantity}, adding: {quantity}")
                        material.quantity += quantity
                    else:
                        logger.info(f"Updating material: {name} with quantity: {quantity}")
                        material.quantity = quantity
                else:
                    logger.info(f"Adding new material: {name} with quantity: {quantity}")
                    new_material = Material(name=name, quantity=quantity)
                    db.session.add(new_material)

            db.session.commit()
            logger.info("Materials updated successfully.")
            return jsonify({"message": "Materials updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating materials: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": "An error occurred while updating materials"}), 500



    @app.route('/material', methods=['GET'])
    def get_materials():
        try:
            materials = Material.query.all()
            logger.info("Materials retrieved successfully")
            return jsonify([
                {"id": m.id, "name": m.name, "quantity": m.quantity}
                for m in materials
            ]), 200
        except Exception as e:
            logger.error(f"Error getting materials! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while getting the materials"}), 500
        
    @app.route('/blueprint/<int:id>', methods=['PUT'])
    def update_blueprint(id):
        try:
            blueprint = Blueprint.query.get_or_404(id)
            data = request.json
            blueprint.name = data.get('name', blueprint.name)
            blueprint.materials = data.get('materials', blueprint.materials)
            blueprint.sell_price = data.get('sell_price', blueprint.sell_price)
            blueprint.max = data.get('max', blueprint.max)
            db.session.commit()
            logger.info("Blueprint updated successfully")
            return jsonify({'message': 'Blueprint updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating blueprint! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while updating the blueprint"}), 500
    
    @app.route('/blueprints/reset_max', methods=['POST'])
    def reset_all_blueprint_max():
        try:
            blueprints = Blueprint.query.all()
            for blueprint in blueprints:
                blueprint.max = None  # Set max to None for ALL blueprints
            db.session.commit()
            logger.info("All blueprint max values have been reset")
            return jsonify({"message": "All blueprint max values have been reset."}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting all blueprint max values! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while resetting max values."}), 500


    @app.route('/blueprint/<int:id>', methods=['DELETE'])
    def delete_blueprint(id):
        try:
            blueprint = Blueprint.query.get_or_404(id)
            db.session.delete(blueprint)
            db.session.commit()
            logger.info("Blueprint deleted successfully")
            return jsonify({"message": "Blueprint deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting blueprint! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while deleting the blueprint"}), 500

    @app.route('/material/<int:id>', methods=['PUT'])
    def update_material(id):
        try:
            data = request.json
            material = Material.query.get_or_404(id)
            material.quantity = data.get('quantity', material.quantity)
            db.session.commit()
            logger.info("Material updated successfully")
            return jsonify({"message": "Material updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating material! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while updating the material"}), 500

    @app.route('/material/<int:id>', methods=['DELETE'])
    def delete_material(id):
        try:
            material = Material.query.get_or_404(id)
            db.session.delete(material)
            db.session.commit()
            logger.info("Material deleted successfully")
            return jsonify({"message": "Material deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting material! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while deleting the material"}), 500

    @app.route('/optimize', methods=['GET'])
    def optimize():
        try:
            blueprints = Blueprint.query.all()
            materials = Material.query.all()
            
            logger.debug(f"Blueprints: {[{'name': b.name, 'sell_price': b.sell_price, 'material_cost': b.material_cost} for b in blueprints]}")
            logger.debug(f"Materials: {[{'name': m.name, 'quantity': m.quantity} for m in materials]}")
    
            if not blueprints:
                logger.error("No blueprints found in the database.")
                return jsonify({"error": "No blueprints available for optimization."}), 400
    
            if not materials:
                logger.error("No materials found in the database.")
                return jsonify({"error": "No materials available for optimization."}), 400
        
    
            prob = LpProblem("Modules Optimization", LpMaximize)
    
            # Define decision variables
            x = {b.name: LpVariable(f"x_{b.name}", lowBound=0, cat='Integer') for b in blueprints}
    
            # Set objective function
            try:
                prob += lpSum((b.sell_price - (b.material_cost or 0)) * x[b.name] for b in blueprints)
            except Exception as e:
                logger.error("Error setting objective function: %s", str(e))
                return jsonify({"error": "Invalid blueprint data (e.g., missing sell_price or material_cost)."}), 400
    
            # Add material constraints
            for m in materials:
                prob += lpSum(b.materials.get(m.name, 0) * x[b.name] for b in blueprints) <= m.quantity
    
            # Add max constraints for blueprints
            for b in blueprints:
                if b.max is not None:
                    prob += x[b.name] <= b.max
    
            
            prob.solve(PULP_CBC_CMD(msg=False))
    
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
                    "true_profit": sum((b.sell_price - (b.material_cost or 0)) * value(x[b.name]) for b in blueprints)
                }
                logger.info("Optimization completed successfully")
                logger.info("Results: %s", results)
                return jsonify(results), 200
            elif LpStatus[prob.status] == 'Unbounded':
                logger.error("Optimization problem is unbounded.")
                return jsonify({"error": "Optimization problem is unbounded. Check your constraints and input data."}), 400
            else:
                logger.error("No optimal solution found.")
                return jsonify({"status": "No optimal solution found"}), 400
    
        except Exception as e:
            logger.error("An error occurred during optimization: %s", str(e))
            logger.error(traceback.format_exc())
            return jsonify({"error": "An error occurred during optimization"}), 500
