from collections import defaultdict
import os
import subprocess
import sys
from flask import jsonify, render_template, request
import logging
import traceback
import re


import pulp
from models import BlueprintT2, db, Blueprint, Material
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
            raw_materials_text = data['materials']
            raw_invention_text = data.get('invention_materials', '')
            sell_price = data['sell_price']
            material_cost = data['material_cost']
            blueprint_tier = data.get('tier', 'T1')
            invention_chance = data.get('invention_chance', None)

            category_lookup = get_material_category_lookup()
            normalized_materials, name, detected_material_cost = parse_blueprint_text(raw_materials_text, category_lookup)

            # T2 invention cost calculation
            invention_materials_dict = {}
            invention_cost = 0
            if blueprint_tier == "T2" and raw_invention_text.strip():
                invention_materials_dict, invention_cost = parse_ingame_invention_text(raw_invention_text)
                if invention_materials_dict:
                    if "Invention Materials" not in normalized_materials:
                        normalized_materials["Invention Materials"] = {}
                    normalized_materials["Invention Materials"].update(invention_materials_dict)
                # Refined invention cost calculation
                if invention_chance and invention_chance > 0:
                    detected_invention_cost = invention_cost / (invention_chance * 10)
                else:
                    detected_invention_cost = 0
                detected_material_cost += detected_invention_cost

            if material_cost == 0 or material_cost is None:
                material_cost = detected_material_cost

            # Save/update logic
            if blueprint_tier == "T2":
                existing = BlueprintT2.query.filter_by(name=name).first()
                if existing:
                    existing.materials = normalized_materials
                    existing.sell_price = sell_price
                    existing.material_cost = material_cost
                    existing.invention_chance = invention_chance,
                    existing.tier = blueprint_tier
                    db.session.commit()
                    return jsonify({"message": "Blueprint updated successfully"}), 200
                new_blueprint = BlueprintT2(
                    name=name,
                    materials=normalized_materials,
                    sell_price=sell_price,
                    material_cost=material_cost,
                    invention_chance=invention_chance,
                    tier= blueprint_tier
                )
            else:
                existing = Blueprint.query.filter_by(name=name).first()
                if existing:
                    existing.materials = normalized_materials
                    existing.sell_price = sell_price
                    existing.material_cost = material_cost,
                    existing.tier = blueprint_tier
                    db.session.commit()
                    return jsonify({"message": "Blueprint updated successfully"}), 200
                new_blueprint = Blueprint(
                    name=name,
                    materials=normalized_materials,
                    sell_price=sell_price,
                    material_cost=material_cost,
                    tier= blueprint_tier
                )
            db.session.add(new_blueprint)
            db.session.commit()
            return jsonify({"message": "Blueprint added successfully"}), 201

        except Exception as e:
            db.session.rollback()
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
            logger.info(f"Blueprint {id} retrieved successfully")
            # Prepare base response
            response = {
                'id': blueprint.id,
                'name': blueprint.name,
                'materials': blueprint.materials,
                'sell_price': blueprint.sell_price,
                'material_cost': blueprint.material_cost,
                'tier': blueprint.tier
            }
            # If T2, add invention_chance
            if blueprint.tier == "T2":
                response['invention_chance'] = getattr(blueprint, 'invention_chance', None)
            return jsonify(response), 200
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
                bp_dict = {
                    "id": b.id,
                    "name": b.name,
                    "materials": materials,
                    "sell_price": b.sell_price,
                    "material_cost": b.material_cost,
                    "tier": b.tier
                }
                if b.tier == "T2":
                    bp_dict["invention_chance"] = getattr(b, "invention_chance", None)
                response.append(bp_dict)
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
            category_lookup = get_material_category_lookup()
            return jsonify([
                {
                    "id": m.id,
                    "name": m.name,
                    "quantity": m.quantity,
                    "category": category_lookup.get(m.name, "Other")
                }
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
            blueprint.material_cost = data.get('material_cost', blueprint.material_cost)
            blueprint.max = data.get('max', blueprint.max)
            blueprint.tier = data.get('tier', blueprint.tier)
            # Only set invention_chance if blueprint is T2
            if blueprint.tier == 'T2':
                blueprint.invention_chance = data.get('invention_chance', blueprint.invention_chance)
            else:
                blueprint.invention_chance = None
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

            # --- Helper: Recursively expand all materials for a blueprint ---
            def expand_materials(bp):
                expanded = defaultdict(int)
                for section in bp.materials.values():
                    for mat, qty in section.items():
                        sub_bp = next((b for b in blueprints if b.name == mat), None)
                        if sub_bp:
                            sub_mats = expand_materials(sub_bp)
                            for sm, sq in sub_mats.items():
                                expanded[sm] += sq * qty
                            # Count the dependency itself (for tracking how many of this component are needed)
                            expanded[mat] += qty
                        else:
                            expanded[mat] += qty
                return expanded

            # --- Collect all unique materials and their categories ---
            all_materials = set()
            material_categories = {}
            for b in blueprints:
                if isinstance(b.materials, dict):
                    for category, sub_category in b.materials.items():
                        if isinstance(sub_category, dict):
                            for material in sub_category.keys():
                                all_materials.add(material)
                                material_categories[material] = category
                else:
                    for material in b.materials.keys():
                        all_materials.add(material)
                        material_categories[material] = "Other"

            # --- Add missing materials to DB with quantity 0 ---
            for material in all_materials:
                if material not in materials:
                    new_material = Material(name=material, quantity=0)
                    db.session.add(new_material)
                    materials[material] = 0
            db.session.commit()

            prob = LpProblem("Modules Optimization", LpMaximize)
            x = {b.name: LpVariable(f"x_{b.name}", lowBound=0, cat='Integer') for b in blueprints}

            # --- Objective function ---
            prob += lpSum((b.sell_price - b.material_cost) * x[b.name] for b in blueprints)

            # --- Material constraints using expanded dependencies ---
            all_required_materials = defaultdict(lambda: 0)
            for b in blueprints:
                expanded = expand_materials(b)
                for mat, qty in expanded.items():
                    all_required_materials[mat] += qty * x[b.name]

            for mat, quantity in materials.items():
                prob += all_required_materials[mat] <= quantity

            # --- Helper: Get material quantity from blueprint (for reporting) ---
            def get_material_quantity(blueprint, material_name):
                if isinstance(blueprint.materials, dict):
                    quantity = 0
                    for sub_category in blueprint.materials.values():
                        if isinstance(sub_category, dict):
                            quantity += sub_category.get(material_name, 0)
                    return quantity
                return blueprint.materials.get(material_name, 0)

            # --- Material constraints (legacy, can be removed if using expanded only) ---
            # for material_name, quantity in materials.items():
            #     prob += lpSum(get_material_quantity(b, material_name) * x[b.name] for b in blueprints) <= quantity

            # --- Max constraints for blueprints ---
            for b in blueprints:
                if b.max is not None:
                    prob += x[b.name] <= b.max

            prob.solve(PULP_CBC_CMD(msg=False))

            logger.info("Optimization Status: %s", LpStatus[prob.status])

            if LpStatus[prob.status] == 'Optimal':
                # --- Calculate dependency quantities ---
                dependency_quantities = defaultdict(int)
                blueprint_names = {bp.name for bp in blueprints}
                for b in blueprints:
                    n_to_produce = int(value(x[b.name]) or 0)
                    if n_to_produce == 0:
                        continue
                    expanded = expand_materials(b)
                    for mat, qty in expanded.items():
                        if mat in blueprint_names:
                            dependency_quantities[mat] += qty * n_to_produce

                results = {
                    "status": "Optimal",
                    "total_profit": sum(b.sell_price * value(x[b.name]) for b in blueprints),
                    "what_to_produce": {b.name: int(value(x[b.name]) or 0) for b in blueprints},
                    "material_usage": {
                        m_name: {
                            "used": sum(get_material_quantity(b, m_name) * int(value(x[b.name]) or 0) for b in blueprints),
                            "remaining": m_qty - sum(get_material_quantity(b, m_name) * int(value(x[b.name]) or 0) for b in blueprints),
                            "category": material_categories.get(m_name, "Other(Likely Unused or other Built Components)")
                        } for m_name, m_qty in materials.items()
                    },
                    "true_profit": sum((b.sell_price - b.material_cost) * value(x[b.name]) for b in blueprints),
                    "dependencies_needed": dict(dependency_quantities)  # <-- {name: qty}
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






def parse_blueprint_text(raw_text, category_lookup=None):
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    if not lines:
        return {}, "Unknown", 0
    # --- ISK/hour format detection ---
    if any("Component Material List" in l for l in lines):
        return parse_iskhour_format(lines, category_lookup)
    # --- In-game format detection ---
    if any("Blueprint" in l and "\t" in l for l in lines):
        return parse_ingame_format(lines)
    # --- Fallback in case of unknown format ---
    return {}, "Unknown", 0


def parse_iskhour_format(lines, category_lookup=None):
    materials_by_category = {}
    blueprint_name = "Unknown"
    section = None
    build_material_cost = 0
    invention_material_cost = 0

    # Extract blueprint name
    for l in lines:
        m = re.match(r".*'(.+?) Blueprint'", l)
        if m:
            blueprint_name = m.group(1)
            break

    # Use a lookup for categories if provided
    if category_lookup is None:
        category_lookup = {}

    for l in lines:
        if l.startswith("Component Material List"):
            section = "Materials"
            continue
        if l.startswith("Invention Materials"):
            section = "Invention Materials"
            continue
        if l.startswith("Material - Quantity"):
            continue
        if l.startswith("Total Volume"):
            continue
        # Extract Material Cost for current section
        if l.startswith("Total Cost of Materials:"):
            try:
                cost_str = l.split(":")[1].strip().replace("ISK", "").replace(",", "")
                if section == "Materials":
                    build_material_cost = float(cost_str)
                elif section == "Invention Materials":
                    invention_material_cost = float(cost_str)
            except Exception:
                pass
            continue
        # Parse materials
        if section and "-" in l:
            try:
                mat, qty = l.rsplit("-", 1)  # <-- FIXED HERE
                mat = mat.strip()
                qty = int(float(qty.strip().replace(",", "")))
                if section == "Materials":
                    cat = category_lookup.get(mat, "Other")
                    if cat == "Blueprint":
                        cat = "Items"
                    if cat not in materials_by_category:
                        materials_by_category[cat] = {}
                    materials_by_category[cat][mat] = qty
                elif section == "Invention Materials":
                    if "Invention Materials" not in materials_by_category:
                        materials_by_category["Invention Materials"] = {}
                    materials_by_category["Invention Materials"][mat] = qty
            except Exception as e:
                logger.error(f"Error parsing line: {l}")
                logger.error(traceback.format_exc())
            continue


    total_material_cost = build_material_cost + invention_material_cost
    return materials_by_category, blueprint_name, total_material_cost


def parse_ingame_invention_text(raw_text):
    """
    Parses invention data from the game, e.g.:
    Datacores				
    Item	Required	Available	Est. Unit price	typeID
    Datacore - Laser Physics	2	0	102179.43	20413
    ...
    Optional items				
    Item	Required	Available	Est. Unit price	typeID
    Parity Decryptor	1	0	1852359.61	34204
    """
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    invention_materials = {}
    total_cost = 0
    section = None

    for l in lines:
        if l.lower().startswith("datacores"):
            section = "Invention Materials"
            continue
        if l.lower().startswith("optional items"):
            section = "Invention Materials"
            continue
        if l.startswith("Item") or l.startswith("Required") or l.startswith("Available") or l.startswith("Est. Unit price") or l.startswith("typeID"):
            continue
        if section and "\t" in l:
            parts = l.split('\t')
            if len(parts) >= 4:
                try:
                    mat = parts[0].strip()
                    qty = int(float(parts[1].strip()))
                    price = float(parts[3].replace(",", ""))
                    invention_materials[mat] = qty
                    total_cost += qty * price
                except Exception:
                    continue
    return invention_materials, total_cost



def parse_ingame_format(lines):
    blueprint_name = lines[0].split('\t')[0].replace(' Blueprint', '')
    normalized = {}
    current_section = None
    total_cost = 0

    for line in lines[1:]:  # Skip the first line (blueprint name)
        clean_line = line.strip()
        if not clean_line:
            continue

        # If the line does not contain tabs, treat it as a section header
        if '\t' not in clean_line:
            current_section = clean_line
            normalized[current_section] = {}
            continue

        # If the line looks like a column header, skip it
        if clean_line.lower().startswith('item\t') or clean_line.lower().startswith('material\t'):
            continue

        # Parse material lines
        if current_section and '\t' in clean_line:
            parts = [p.strip() for p in clean_line.split('\t')]
            if len(parts) < 2:
                continue
            try:
                mat_name = parts[0]
                quantity = int(float(parts[1]))
                normalized[current_section][mat_name] = quantity

                # Calculate cost if available (4th column)
                if len(parts) >= 4 and parts[3]:
                    unit_price = float(parts[3].replace(",", ""))
                    total_cost += quantity * unit_price
            except Exception:
                continue

    return normalized, blueprint_name, total_cost


def get_material_category_lookup():
    lookup = {}
    blueprints = Blueprint.query.all()
    
    # First pass: Add known minerals
    known_minerals = {'Tritanium', 'Pyerite', 'Mexallon', 'Isogen', 
                     'Nocxium', 'Zydrine', 'Megacyte', 'Morphite'}
    for mineral in known_minerals:
        lookup[mineral] = "Minerals"
        
    # Second pass: Add blueprint materials (newer entries overwrite older ones)
    for bp in reversed(blueprints):  # Reverse to prioritize newer entries
        if isinstance(bp.materials, dict):
            for category, materials in bp.materials.items():
                if isinstance(materials, dict):
                    for mat in materials:
                        lookup[mat] = category
    return lookup


