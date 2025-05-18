import os
import subprocess
import sys
from flask import jsonify, render_template, request
import logging
import traceback


import pulp
from models import db, Blueprint, Material
from pulp import LpProblem, LpVariable, lpSum, value, LpMaximize, LpStatus, PULP_CBC_CMD

# Add the ManuOptimizer package to the Python path
if getattr(sys, 'frozen', False):
    # Running from EXE
    sys.path.append(os.path.join(sys._MEIPASS, '..'))
else:
    # Running from script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
    
    # Register the mining optimizer flask blueprint
    
    # from .MinaOptimizer.routes import mining_planner
    # app.register_blueprint(mining_planner)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    import re

    @app.route('/blueprint', methods=['POST'])
    def add_blueprint():
        try:
            data = request.json
            name = data['name']
            raw_materials_text = data['materials']  # This is now the RAW text.
            sell_price = data['sell_price']
            material_cost = data['material_cost']
    
            normalized_materials = {}
            current_category = None
            total_material_cost = 0  # Initialize material cost
    
            lines = raw_materials_text.splitlines()  # Split into lines
            for line in lines:
                line = line.strip()
                if not line:
                    continue  # Skip empty lines
    
                # Category Detection (Regex)
                if re.match(r'^\s*[A-Za-z\s]+$', line) and not any(
                        keyword in line for keyword in ["Item", "Required", "Available", "Est.", "Unit", "typeID"]):
                    current_category = line.strip()
                    normalized_materials[current_category] = {}  # Initialize if necessary (safety check)
                    continue
    
                if current_category and not re.match(r'^\s*[A-Za-z\s]+$', line):
                    parts = line.split('\t', 1)
                    if len(parts) >= 2:
                        try:
                            material_name = parts[0].strip() #Extract mat name
                            quantity = int(parts[1].split('\t')[0]) #Extract quantity
                            unit_price = float(parts[1].split('\t')[2])  # Extract unit price
                            if current_category not in normalized_materials:
                                normalized_materials[current_category] = {}  # Safety check.
                            normalized_materials[current_category][material_name] = quantity
                            if material_cost == 0:
                                total_material_cost += quantity * unit_price  # Accumulate cost
                        except (ValueError, IndexError):
                            # Handle cases where parsing fails for a line. Log it.
                            logger.warning(f"Skipping unparseable line: {line}")
                            continue
    
                # Skip lines that don't match the category detection regex when current_category is not None
                if current_category and re.match(r'^\s*[A-Za-z\s]+$', line):
                    continue
    
            existing_blueprint = Blueprint.query.filter_by(name=name).first()
            if existing_blueprint:
                existing_blueprint.materials = normalized_materials
                existing_blueprint.sell_price = sell_price
                existing_blueprint.material_cost = total_material_cost  # SET the calculated cost
                db.session.commit()
                logger.info(f"Blueprint: {name} was updated successfully")
                return jsonify({"message": "Blueprint updated successfully"}), 200
    
            new_blueprint = Blueprint(
                name=name,
                materials=normalized_materials,
                sell_price=sell_price,
                material_cost= material_cost if material_cost != -1 else total_material_cost
            )
            db.session.add(new_blueprint)
            db.session.commit()
            logger.info(f"Blueprint: {name} was added successfully")
            return jsonify({"message": "Blueprint added successfully"}), 201
    
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding blueprint! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500

    @app.route('/blueprint/manual', methods=['POST'])
    def add_manual_blueprint():
        try:
            data = request.json
            name = data['name']
            materials = data['materials']
            sell_price = data['sell_price']
            material_cost = data['material_cost']
    
            # Initialize the normalized materials dictionary
            normalized_materials = {}
    
            # Loop through the materials and normalize them
            for category, category_materials in materials.items():
                normalized_materials[category] = {}
                for material, quantity in category_materials.items():
                    normalized_materials[category][material] = quantity
    
            # Check if a blueprint with the same name already exists
            existing_blueprint = Blueprint.query.filter_by(name=name).first()
            if existing_blueprint:
                existing_blueprint.materials = normalized_materials
                existing_blueprint.sell_price = sell_price
                existing_blueprint.material_cost = material_cost
                db.session.commit()
                logger.info(f"Blueprint: {name} was updated successfully")
                return jsonify({"message": "Blueprint updated successfully"}), 200
    
            # Create a new blueprint
            new_blueprint = Blueprint(
                name=name,
                materials=normalized_materials,
                sell_price=sell_price,
                material_cost=material_cost
            )
            db.session.add(new_blueprint)
            db.session.commit()
            logger.info(f"Blueprint: {name} was added successfully")
            return jsonify({"message": "Blueprint added successfully"}), 201
    
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding blueprint! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500

    @app.route('/blueprint/<int:id>', methods=['GET'])
    def get_blueprint(id):
        try:
            blueprint = Blueprint.query.get_or_404(id)
            return jsonify({
                'id': blueprint.id,
                'name': blueprint.name,
                'materials': blueprint.materials,
                'sell_price': blueprint.sell_price,
                'material_cost': blueprint.material_cost   
            }), 200
        except Exception as e:
            logger.error(f"Error getting blueprint! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'An error occurred while getting the blueprint'
            }), 500
    

    @app.route('/blueprints', methods=['GET'])
    def get_blueprints():
        try:
            blueprints = Blueprint.query.all()
            logger.info("Blueprints retrieved successfully")
            response = []
            for b in blueprints:
                materials = []
                for category, quantities in b.materials.items():
                    materials.append({category: quantities})
                response.append({
                    "id": b.id,
                    "name": b.name,
                    "materials": materials,
                    "sell_price": b.sell_price,
                    "material_cost": b.material_cost
                })
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error getting blueprints! See the traceback for more info:")
            logger.error(traceback.format_exc())
            return jsonify({"ERROR": "An error occurred while getting the blueprints"}), 500

    @app.route('/material', methods=['POST'])
    def add_material():
        try:
            data = request.form
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
                # Add new materials
                for name, quantity in materials.items():
                    new_material = Material(name=name, quantity=quantity)
                    db.session.add(new_material)
                db.session.commit()
                logger.info("Materials updated successfully.")
    
            elif update_type == 'add':
                # Replace existing materials with the same name and add new ones
                for name, quantity in materials.items():
                    material = Material.query.filter_by(name=name).first()
                    if material:
                        logger.info(f"Replacing material: {name} with quantity: {quantity}")
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
            materials = {m.name: m.quantity for m in Material.query.all()}
            
            if not blueprints or not materials:
                return jsonify({"status": "No optimal solution found"}), 400

            # Collect all unique materials from blueprints
            all_materials = set()
            material_categories = {}  # Map material names to their categories
            for b in blueprints:
                if isinstance(b.materials, dict):
                    for category, sub_category in b.materials.items():
                        if isinstance(sub_category, dict):
                            for material in sub_category.keys():
                                all_materials.add(material)
                                material_categories[material] = category  # Map material to its category
                else:
                    for material in b.materials.keys():
                        all_materials.add(material)
                        material_categories[material] = "Other"

            # Add missing materials to the database with quantity 0
            for material in all_materials:
                if material not in materials:
                    new_material = Material(name=material, quantity=0)
                    db.session.add(new_material)
                    materials[material] = 0
            db.session.commit()

            prob = LpProblem("Modules Optimization", LpMaximize)
            x = {b.name: LpVariable(f"x_{b.name}", lowBound=0, cat='Integer') for b in blueprints}

            # Objective function
            prob += lpSum((b.sell_price - b.material_cost) * x[b.name] for b in blueprints)

            # Helper function to get material quantity from blueprint
            def get_material_quantity(blueprint, material_name):
                if isinstance(blueprint.materials, dict):
                    quantity = 0
                    for sub_category in blueprint.materials.values():
                        if isinstance(sub_category, dict):
                            quantity += sub_category.get(material_name, 0)
                    return quantity
                return blueprint.materials.get(material_name, 0)

            # Material constraints
            for material_name, quantity in materials.items():
                prob += lpSum(get_material_quantity(b, material_name) * x[b.name] for b in blueprints) <= quantity
                logger.info(f"Added material constraint for {material_name} with quantity {quantity}")

            # Max constraints for blueprints
            for b in blueprints:
                if b.max is not None:
                    prob += x[b.name] <= b.max

            prob.solve(PULP_CBC_CMD(msg=False))
            
            logger.info("Optimizaiton Status: %s", LpStatus[prob.status])

            if LpStatus[prob.status] == 'Optimal':
                results = {
                    "status": "Optimal",
                    "total_profit": sum(b.sell_price * value(x[b.name]) for b in blueprints),
                    "what_to_produce": {b.name: value(x[b.name]) for b in blueprints},
                    "material_usage": {
                        m_name: {
                            "used": sum(get_material_quantity(b, m_name) * int(value(x[b.name])) for b in blueprints),
                            "remaining": m_qty - sum(get_material_quantity(b, m_name) * int(value(x[b.name])) for b in blueprints),
                            "category": material_categories.get(m_name, "Other(Likely Unused or other Built Components)")
                        } for m_name, m_qty in materials.items()
                    },
                    "true_profit": sum((b.sell_price - b.material_cost) * value(x[b.name]) for b in blueprints)
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
