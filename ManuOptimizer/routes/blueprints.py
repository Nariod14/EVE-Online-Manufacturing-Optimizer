from collections import defaultdict
import os
import subprocess
import sys
from flask import jsonify, render_template, request
import logging
import traceback
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


import pulp
from .utils import expand_materials, get_material_category_lookup, get_material_quantity, parse_blueprint_text, parse_ingame_invention_text
from models import BlueprintT2,Blueprint as BlueprintModel, db, Material
from flask import Blueprint
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

blueprints_bp = Blueprint('blueprints', __name__,url_prefix='/api/blueprints')
@blueprints_bp.route('/blueprint', methods=['POST'])
def add_blueprint():
    try:
        data = request.json
        raw_materials_text = data['materials']
        raw_invention_text = data.get('invention_materials', '')
        sell_price = data['sell_price']
        material_cost = data['material_cost']
        blueprint_tier = data.get('tier', 'T1')
        invention_chance = data.get('invention_chance', None)
        runs_per_copy = int(data.get('runs_per_copy', 10))


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
                detected_invention_cost = invention_cost / (invention_chance * runs_per_copy)
            else:
                detected_invention_cost = 0
            
            
            full_material_cost = detected_material_cost + detected_invention_cost

        if material_cost == 0 or material_cost is None:
            material_cost = detected_material_cost

        # Save/update logic
        if blueprint_tier == "T2":
            existing = BlueprintT2.query.filter_by(name=name).first()
            if existing:
                existing.materials = normalized_materials
                existing.sell_price = sell_price
                existing.material_cost = material_cost
                existing.full_material_cost = full_material_cost
                existing.invention_chance = invention_chance
                existing.invention_cost = invention_cost
                existing.tier = blueprint_tier
                existing.runs_per_copy = runs_per_copy
                
                db.session.commit()
                return jsonify({"message": "Blueprint updated successfully"}), 200
            new_blueprint = BlueprintT2(
                name=name,
                materials=normalized_materials,
                sell_price=sell_price,
                material_cost= material_cost,
                full_material_cost=full_material_cost,
                invention_chance=invention_chance,
                invention_cost= invention_cost,
                tier= blueprint_tier,
                runs_per_copy=runs_per_copy
                
            )
        else:
            existing = BlueprintModel.query.filter_by(name=name).first()
            if existing:
                existing.materials = normalized_materials
                existing.sell_price = sell_price
                existing.material_cost = material_cost
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
        logger.info(f"Blueprint: {name} was added successfully")
        return jsonify({"message": "Blueprint added successfully"}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding blueprint! See the traceback for more info:")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500




@blueprints_bp.route('/blueprint/manual', methods=['POST'])
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
        existing_blueprint = BlueprintModel.query.filter_by(name=name).first()
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

@blueprints_bp.route('/blueprint/<int:id>', methods=['GET'])
def get_blueprint(id):
    try:
        blueprint = BlueprintModel.query.get_or_404(id)
        logger.info(f"Blueprint {id} retrieved successfully")
        # Prepare base response
        response = {
            'id': blueprint.id,
            'name': blueprint.name,
            'materials': blueprint.materials,
            'sell_price': blueprint.sell_price,
            'material_cost': blueprint.material_cost,
            'tier': blueprint.tier,
            'invention_chance': getattr(blueprint, 'invention_chance', None),
            'invention_cost': getattr(blueprint, 'invention_cost', None)
        }
        # If T2, add invention_chance
        if blueprint.tier == "T2":
            response['invention_chance'] = getattr(blueprint, 'invention_chance', None)
            response['invention_cost'] = getattr(blueprint, 'invention_cost', None)
            response['full_material_cost'] = getattr(blueprint, 'full_material_cost', None)
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error getting blueprint! See the traceback for more info:")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'An error occurred while getting the blueprint'
        }), 500

@blueprints_bp.route('/blueprints', methods=['GET'])
def get_blueprints():
    try:
        blueprints = BlueprintModel.query.all()
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
                bp_dict["invention_cost"] = getattr(b, "invention_cost", None)
                bp_dict["full_material_cost"] = getattr(b, "full_material_cost", None)
            response.append(bp_dict)
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error getting blueprints! See the traceback for more info:")
        logger.error(traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while getting the blueprints"}), 500


@blueprints_bp.route('/blueprint/<int:id>', methods=['PUT'])
def update_blueprint(id):
    try:
        blueprint = BlueprintModel.query.get_or_404(id)
        data = request.json

        blueprint.name = data.get('name', blueprint.name)
        blueprint.materials = data.get('materials', blueprint.materials)
        blueprint.sell_price = data.get('sell_price', blueprint.sell_price)
        blueprint.material_cost = data.get('material_cost', blueprint.material_cost)
        blueprint.max = data.get('max', blueprint.max)
        blueprint.tier = data.get('tier', blueprint.tier)
        blueprint.runs_per_copy = data.get('runs_per_copy', 10)

        if blueprint.tier == 'T2':
            # Always update invention_chance and invention_cost if provided
            if 'invention_chance' in data and data['invention_chance'] is not None:
                blueprint.invention_chance = data['invention_chance']
            if 'invention_cost' in data and data['invention_cost'] is not None:
                blueprint.invention_cost = data['invention_cost']

            # Always recalculate material_cost to include the new invention cost per run
            base_material_cost = data.get('material_cost', blueprint.material_cost)
            if blueprint.invention_chance and blueprint.invention_cost:
                invention_cost_per_run = blueprint.invention_cost / (blueprint.invention_chance * blueprint.runs_per_copy)
                blueprint.full_material_cost = base_material_cost + invention_cost_per_run
            else:
                blueprint.material_cost = base_material_cost
        else:
            blueprint.invention_chance = None
            blueprint.invention_cost = None


        db.session.commit()
        logger.info("Blueprint updated successfully")
        return jsonify({'message': 'Blueprint updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating blueprint! See the traceback for more info:")
        logger.error(traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while updating the blueprint"}), 500



@blueprints_bp.route('/blueprints/reset_max', methods=['POST'])
def reset_all_blueprint_max():
    try:
        blueprints = BlueprintModel.query.all()
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


@blueprints_bp.route('/blueprint/<int:id>', methods=['DELETE'])
def delete_blueprint(id):
    try:
        blueprint = BlueprintModel.query.get_or_404(id)
        db.session.delete(blueprint)
        db.session.commit()
        logger.info("Blueprint deleted successfully")
        return jsonify({"message": "Blueprint deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting blueprint! See the traceback for more info:")
        logger.error(traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while deleting the blueprint"}), 500
    

@blueprints_bp.route('/optimize', methods=['GET'])
def optimize():
    try:
        blueprints = BlueprintModel.query.all()
        materials = {m.name: m.quantity for m in Material.query.all()}

        if not blueprints or not materials:
            return jsonify({"status": "No optimal solution found"}), 400

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
        t1_dependencies = defaultdict(float)
        for b in blueprints:
            expanded = expand_materials(b, blueprints, quantity=1, t1_dependencies=t1_dependencies)
            for mat, qty in expanded.items():
                all_required_materials[mat] += qty * x[b.name]

        for mat, quantity in materials.items():
            prob += all_required_materials[mat] <= quantity

        # --- Max constraints for blueprints ---
        for b in blueprints:
            if b.max is not None:
                prob += x[b.name] <= b.max

        prob.solve(PULP_CBC_CMD(msg=False))

        logger.info("Optimization Status: %s", LpStatus[prob.status])

        if LpStatus[prob.status] == 'Optimal':
            dependencies_needed = defaultdict(float)
            for b in blueprints:
                n_to_produce = int(value(x[b.name]) or 0)
                if n_to_produce == 0:
                    continue
                t1_deps = defaultdict(float)
                expand_materials(b, blueprints, quantity=n_to_produce, t1_dependencies=t1_deps)
                for t1_name, qty in t1_deps.items():
                    dependencies_needed[t1_name] += qty
                    
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
                "dependencies_needed": {k: int(v) for k, v in dependencies_needed.items() if v > 0}
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
