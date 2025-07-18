from collections import defaultdict
from copy import deepcopy
import os
import subprocess
import sys
import concurrent
from flask import jsonify, render_template, request, session
import logging
import traceback
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


import pulp
from .utils import accumulate_materials, compute_expanded_materials, expand_materials, expand_materials_clean, expand_sub_blueprints_one_level, fetch_price, get_lowest_jita_sell_price, get_lowest_jita_sell_prices_loop, get_material_category_lookup, get_item_info, get_material_quantity, normalize_materials_structure, normalize_name, parse_blueprint_text, parse_ingame_invention_text, refresh_access_token, safe_subtract, sanitize_name, validate_inventory
from models import BlueprintT2, Blueprint as BlueprintModel, Station, db, Material
from flask import Blueprint
from pulp import LpProblem, LpVariable, lpSum, value, LpMaximize, LpStatus, PULP_CBC_CMD, LpAffineExpression





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
@blueprints_bp.route('/blueprints', methods=['POST'])
def add_blueprint():
    try:
        data = request.json
        raw_blueprint_paste = data['blueprint_paste']
        raw_invention_paste = data.get('invention_materials', '')
        sell_price = data.get('sell_price', 0)
        material_cost = data.get('material_cost', 0)
        blueprint_tier = data.get('tier', 'T1')
        invention_chance = data.get('invention_chance', None)
        runs_per_copy_raw = data.get('runs_per_copy')
        runs_per_copy = int(runs_per_copy_raw) if runs_per_copy_raw is not None else None

        
        
        headers = {
            'User-Agent': 'ManuOptimizer 1.0 nariod14@gmail.com'
        }


        category_lookup = get_material_category_lookup()
        normalized_materials, name = parse_blueprint_text(raw_blueprint_paste, category_lookup)
        logger.info(f"Parsed blueprint name: {name}")
        
        blueprint_info = get_item_info([name])
        typeID = blueprint_info.get(normalize_name(name), {}).get("type_id", 0)
        
        if not typeID:
            logger.warning(f"Blueprint name not found in SDE: {name}, unable to resolve typeID.")
            return jsonify({"error": f"Blueprint name not found in SDE: {name}, unable to resolve typeID. This shouldnt happen, please report this on github issues."}), 400

        
        # Get cost and sell price
        if sell_price == 0 or sell_price is None:
            sell_price = get_lowest_jita_sell_price(typeID, headers=headers)[0] * runs_per_copy
        
        if not material_cost:
            # Step 1: Flatten material names
            material_names = [
                item_name
                for category in normalized_materials.values()
                for item_name in category.keys()
            ]

            # Step 1: Get type IDs from names
            material_info = get_item_info(material_names)
            type_id_map = {
                normalize_name(name): info["type_id"]
                for name, info in material_info.items()
            }

            # Step 2: Fetch prices using your working loop method
            type_ids = list(set(type_id_map.values()))
            price_map = get_lowest_jita_sell_prices_loop(type_ids, headers=headers)

            # Step 3: Total up cost
            material_cost = 0
            for category, materials in normalized_materials.items():
                for mat_name, quantity in materials.items():
                    norm = normalize_name(mat_name)
                    tid = type_id_map.get(norm)
                    unit_price = price_map.get(tid, 0.0)
                    material_cost += quantity * unit_price



        # T2 invention cost calculation
        invention_materials_dict = {}
        invention_cost = 0
        if blueprint_tier == "T2" and raw_invention_paste.strip():
            invention_materials_dict, invention_cost = parse_ingame_invention_text(raw_invention_paste)
            if invention_materials_dict:
                if "Invention Materials" not in normalized_materials:
                    normalized_materials["Invention Materials"] = {}
                normalized_materials["Invention Materials"].update(invention_materials_dict)
              
            if invention_chance and invention_chance > 1:
                invention_chance /= 100
            # Refined invention cost calculation
            if invention_chance and invention_chance > 0:
                detected_invention_cost = invention_cost / (invention_chance * runs_per_copy)
            else:
                detected_invention_cost = 0
            
            
            full_material_cost = material_cost + detected_invention_cost

        # Save/update logic
        if blueprint_tier == "T2":
            existing = BlueprintT2.query.filter_by(name=name).first()
            if existing:
                existing.type_id = typeID
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
                type_id=typeID,
                materials=normalized_materials,
                sell_price=sell_price,
                material_cost= material_cost,
                full_material_cost=full_material_cost,
                invention_chance=invention_chance,
                invention_cost= invention_cost,
                tier= blueprint_tier,
                runs_per_copy=runs_per_copy
                
            )
        else: # T1 case
            existing = BlueprintModel.query.filter_by(name=name).first()
            if existing:
                existing.materials = normalized_materials
                existing.sell_price = sell_price
                existing.material_cost = material_cost
                existing.tier = blueprint_tier
                db.session.commit()
                return jsonify({"message": "Blueprint updated successfully"}), 200
            new_blueprint = BlueprintModel(
                name=name,
                type_id=typeID,
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
            "station_id": getattr(blueprint, 'station_id', None),
            "use_jita_sell": getattr(blueprint, 'use_jita_sell', True),
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
            normalized = normalize_materials_structure(b.materials)

            for category, quantities in normalized.items():
                for name, quantity in quantities.items():
                    materials.append({
                        "name": name,
                        "quantity": quantity / b.amt_per_run,
                        "category": category
                    })
            bp_dict = {
                "id": b.id,
                "name": b.name,
                "materials": materials,
                "sell_price": b.sell_price,
                "amt_per_run": b.amt_per_run,
                "material_cost": b.material_cost / b.amt_per_run,
                "tier": b.tier,
                "station_id": b.station_id,
                "station_name": b.station.name if b.station else None,
                "use_jita_sell": b.use_jita_sell,
                "used_jita_fallback": getattr(b, 'used_jita_fallback', False)
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
        blueprint.amt_per_run = data.get('amt_per_run', blueprint.amt_per_run)
        blueprint.material_cost = data.get('material_cost', blueprint.material_cost)
        blueprint.max = data.get('max', blueprint.max)
        blueprint.tier = data.get('tier', blueprint.tier)
        blueprint.station_id = data.get('station_id', blueprint.station_id)

        # Jita logic
        if blueprint.station_id is not None and blueprint.station_id != 60003760:
            blueprint.use_jita_sell = False
        else:
            blueprint.use_jita_sell = True

        # Optional T2-specific logic
        if blueprint.tier == 'T2':
            if 'invention_chance' in data and data['invention_chance'] is not None:
                blueprint.invention_chance = data['invention_chance']
            if 'invention_cost' in data and data['invention_cost'] is not None:
                blueprint.invention_cost = data['invention_cost']
            if 'runs_per_copy' in data and data['runs_per_copy'] is not None:
                blueprint.runs_per_copy = data['runs_per_copy']

            base_material_cost = blueprint.material_cost
            if blueprint.invention_chance and blueprint.invention_cost:
                invention_cost_per_run = blueprint.invention_cost / (blueprint.invention_chance * blueprint.runs_per_copy)
                blueprint.full_material_cost = base_material_cost + invention_cost_per_run
            else:
                blueprint.full_material_cost = base_material_cost
        else:
            blueprint.invention_chance = None
            blueprint.invention_cost = None

        db.session.commit()
        logger.info("Blueprint updated successfully")
        return jsonify({'message': 'Blueprint updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error("Error updating blueprint! See the traceback for more info:")
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
                
@blueprints_bp.route('/update_prices', methods=['POST'])
def update_prices():
    try:
        access_token = session.get("token")
        headers = {
            'User-Agent': 'ManuOptimizer 1.0 nariod14@gmail.com'
        }
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
            
            test = requests.get("https://esi.evetech.net/verify", headers=headers)
            if test.status_code == 401:
                # token expired — try refreshing
                access_token = refresh_access_token()
                if not access_token:
                    logger.error("Token refresh failed. User must re-authenticate.")
                    return jsonify({"error": "Login expired, please re-authenticate"}), 403
                headers["Authorization"] = f"Bearer {access_token}"

    

        materials = Material.query.all()
        blueprints = BlueprintModel.query.all()
        
        
        # Prepopulate missing type_ids from normalized material names
        all_needed_names = set()
        for bp in blueprints:
            normalized = bp.get_normalized_materials()
            for category in normalized.values():
                all_needed_names.update(category.keys())


        # Fetch missing type_ids
        unique_type_ids = {mat.type_id for mat in materials if mat.type_id}
        # Get existing name->type_id from DB
        existing_name_to_id = {mat.name: mat.type_id for mat in materials if mat.type_id}

        # Identify missing ones
        missing_names = [name for name in all_needed_names if name not in existing_name_to_id]
        
       

        if missing_names:
            lookup_result = get_item_info(missing_names)
            for name in missing_names:
                norm = normalize_name(name)
                if norm in lookup_result:
                    tid = lookup_result[norm]['type_id']
                    existing_name_to_id[name] = tid
                    unique_type_ids.add(tid)
                    # Optionally, you can add these missing materials to DB here if you want
                    # or just keep this mapping for price fetching
                    logger.info(f"Resolved missing type_id for '{name}': {tid}")
                else:
                    logger.warning(f"Could not resolve type_id for '{name}'")

        
        
        # Stage material fetch jobs
        material_jobs = [(tid, None) for tid in unique_type_ids]
        blueprint_jobs = []
        # Stage blueprint fetch jobs
        for bp in blueprints:
            if not bp.type_id:
                info = get_item_info([bp.name])
                norm_name = normalize_name(bp.name)
                if norm_name in info:
                    bp.type_id = info[norm_name]['type_id']
                    unique_type_ids.add(bp.type_id)
                else:
                    logger.warning(f"Could not resolve type_id for blueprint '{bp.name}'")
                    continue  # Skip blueprint if no type_id

            if not bp.use_jita_sell and bp.station_id:
                blueprint_jobs.append((bp.type_id, bp.station_id))
            else:
                blueprint_jobs.append((bp.type_id, None))

        prices = {}
        fallback_flags = {}  # Track if fallback to Jita happened

        
        jobs = material_jobs + blueprint_jobs
        

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_price, tid, sid, headers): tid for tid, sid in jobs}
            for future in concurrent.futures.as_completed(futures):
                tid, price_tuple, fallback = future.result()
                price, source = price_tuple  # unpack the tuple

                if price is not None:
                    prices[tid] = price_tuple  # store tuple (price, source)
                    fallback_flags[tid] = fallback
                else:
                    logger.warning(f"No price found for type_id {tid} — source: {source}")

        # Cache all material prices (including invention materials)
        material_price_map = {}

        for mat in materials:
            price_data = prices.get(mat.type_id)
            if price_data:
                mat.sell_price = price_data[0]
                material_price_map[mat.type_id] = mat.sell_price
            else:
                if mat.category != "Invention Materials":
                    logger.warning(f"No price found for material {mat.name} (type_id: {mat.type_id})")


        for bp in blueprints:
            price_data = prices.get(bp.type_id)

            if price_data:
                bp.sell_price = price_data[0]
                bp.used_jita_fallback = fallback_flags.get(bp.type_id, False)
            else:
                logger.warning(f"No price found for blueprint {bp.name} (type_id: {bp.type_id})")
                bp.sell_price = None
                bp.used_jita_fallback = False

            total_cost = 0.0
            invention_cost = 0.0
            
            

            name_to_type_id = existing_name_to_id
            type_id_to_price = {mat.type_id: prices.get(mat.type_id, (None,))[0] for mat in materials}
            
            for bp in blueprints:
                total_cost = 0.0
                invention_cost = 0.0

                name_to_type_id = existing_name_to_id
                type_id_to_price = {
                    tid: prices.get(tid, (None,))[0]
                    for tid in name_to_type_id.values()
                    if tid is not None
                }

                normalized = bp.get_normalized_materials()

                for category, materials_dict in normalized.items():
                    for mat_name, qty in materials_dict.items():
                        type_id = name_to_type_id.get(mat_name)
                        unit_price = type_id_to_price.get(type_id)

                        if unit_price is None:
                            logger.warning(f"No price for material {mat_name} (type_id: {type_id}) in blueprint {bp.name}")
                            continue

                        if category == "Invention Materials":
                            invention_cost += unit_price * qty
                        else:
                            total_cost += unit_price * qty

                bp.material_cost = round(total_cost, 2)

                # Full material cost calculation
                if bp.tier == 'T2' and bp.invention_chance and bp.runs_per_copy:
                    try:
                        invention_chance_decimal = bp.invention_chance / 100.0 if bp.invention_chance > 1 else bp.invention_chance
                        invention_cost_per_run = invention_cost / (invention_chance_decimal * bp.runs_per_copy) if invention_chance_decimal > 0 else 0
                        bp.full_material_cost = round(bp.material_cost + invention_cost_per_run, 2)
                    except ZeroDivisionError:
                        bp.full_material_cost = bp.material_cost
                        logger.warning(f"ZeroDivisionError in invention cost calculation for {bp.name}")
                else:
                    bp.full_material_cost = bp.material_cost



        db.session.commit()
        return jsonify({"message": "Prices updated successfully"}), 200

    except Exception:
        db.session.rollback()
        logger.error("Error updating prices", exc_info=True)
        return jsonify({"error": "An error occurred while updating prices"}), 500





@blueprints_bp.route('/optimize', methods=['GET'])
def optimize():
    try:
        blueprints = BlueprintModel.query.all()
        material_objs = {m.name: m for m in Material.query.all()}
        inventory = {name: m.quantity for name, m in material_objs.items()}
        untouched_inventory = {name: m.quantity for name, m in material_objs.items()}
        
        if not blueprints or not inventory:
            return jsonify({"status": "No optimal solution found"}), 400

        logger.info("Materials loaded: %s", inventory)
        bp_names = {b.name for b in blueprints}

        # 1. Create mappings between original and sanitized names for consistent lookups
        # We need this to display final results with the original "pretty" names
        s_name_to_original = {
            **{sanitize_name(b.name): b.name for b in blueprints},
            **{sanitize_name(m.name): m.name for m in material_objs.values()}
        }

        # Create a version of the inventory with sanitized keys for the model
        sanitized_inventory = {sanitize_name(name): qty for name, qty in inventory.items()}

        # 2. Create decision variables using SANITIZED names
        # The LpVariable name AND the dictionary key must be sanitized and identical.
        x = {sanitize_name(b.name): LpVariable(sanitize_name(b.name), lowBound=0, cat='Integer') for b in blueprints}

        prob = LpProblem("MaxProfit", LpMaximize)

        # 3. Calculate profit and build the objective function using SANITIZED names
        profit_per_bp = {}
        for b in blueprints:
            s_name = sanitize_name(b.name)
            profit_per_bp[s_name] = (b.sell_price - (b.full_material_cost if b.tier == 'T2' else b.material_cost)) / b.amt_per_run

        prob += lpSum(profit_per_bp[s_name] * x[s_name] for s_name in x.keys())

        # 4. Calculate material consumption and production using SANITIZED names
        consumption = defaultdict(LpAffineExpression)
        production = defaultdict(LpAffineExpression)

        for b in blueprints:
            s_bp_name = sanitize_name(b.name)
            quantity_per_run = getattr(b, "amt_per_run", 1)

            # Production: This blueprint produces itself
            production[s_bp_name] += quantity_per_run * x[s_bp_name]

            # Consumption: This blueprint consumes its materials
            normalized_mats = normalize_materials_structure(b.materials) if isinstance(b.materials, list) else b.materials

            for section_name, section in normalized_mats.items():
                for mat_name, qty_per_run in section.items():
                    s_mat_name = sanitize_name(mat_name)
                    consumption[s_mat_name] += qty_per_run * x[s_bp_name]

        # 5. The UNIFIED material balance constraint using SANITIZED names
        # This is the logic that fixes your inventory issue.
        all_sanitized_items = set(sanitized_inventory.keys()) | set(consumption.keys()) | set(production.keys())

        for s_item_name in all_sanitized_items:
            consumed_expr = consumption.get(s_item_name, 0)
            produced_expr = production.get(s_item_name, 0)
            inventory_qty = sanitized_inventory.get(s_item_name, 0)

            # Constraint: Total Consumed - Total Produced <= Starting Inventory
            prob += consumed_expr - produced_expr <= inventory_qty, f"MaterialBalance_{s_item_name}"

        # 6. Max production constraints using SANITIZED names
        for b in blueprints:
            if b.max is not None:
                s_name = sanitize_name(b.name)
                prob += x[s_name] <= b.max, f"MaxProd_{s_name}"
                
                
        logger.info("Solving optimization problem...")
        prob.solve(PULP_CBC_CMD(msg=False))

        if LpStatus[prob.status] != 'Optimal':
            logger.info("Optimization status: %s", LpStatus[prob.status])
            # Save the LP file for debugging non-optimal solutions
            with open("lp_debug_output.lp", "w") as f:
                f.write(str(prob))
            return jsonify({"status": f"No optimal solution found: {LpStatus[prob.status]}"}), 400

        # Save the LP file for inspection of the successful run
        with open("lp_output.lp", "w") as f:
            f.write(str(prob))

        # Optimization results - convert sanitized names back to original names for the response
        what_to_produce = {
            s_name_to_original[s_name]: int(value(var) or 0)
            for s_name, var in x.items()
            if (value(var) or 0) > 0  # Only include items we are actually producing
        }

        logger.info("Optimal production: %s", what_to_produce)
        logger.info("Objective value: %s", value(prob.objective))

        # === Dependency resolution with inventory awareness ===

        # Step 1: Build intermediate dependencies first (inventory-aware)
        total_needed = defaultdict(int)  # Materials (minerals/components/etc.)
        item_needs = defaultdict(int)    # Items to build (intermediates)
        used_from_inv_total = defaultdict(int)
        final_produced = defaultdict(int)
        produced = defaultdict(int)
        remaining_inventory = inventory.copy()

        # Set to track processed blueprints
        processed_blueprints = set()

        # === Pass 1: Expand dependencies BEFORE handling top-level "what_to_produce" ===
        for b in blueprints:
            count = what_to_produce.get(b.name, 0)
            if count > 0:
                produced[b.name] += count

        logger.info("Initial production plan: %s", produced)  # Log produced quantities

        # === Dependency resolution phase ===
        # Accumulate all materials and intermediate item needs from the initial production plan
        for b in blueprints:
            count = produced.get(b.name, 0)
            if count > 0 and b.name not in processed_blueprints:
                accumulate_materials(b, count, total_needed, item_needs, blueprints)
                processed_blueprints.add(b.name)  # Mark this blueprint as processed

        # Now subtract inventory from intermediate items first
        to_build = defaultdict(int)
        for name, qty_needed in item_needs.items():
            inv_qty = remaining_inventory.get(name, 0)
            used = min(inv_qty, qty_needed)
            if used > 0:
                used_from_inv_total[name] = used
                remaining_inventory[name] -= used
            if qty_needed > used:
                to_build[name] = qty_needed - used

        # Recursively build what's still missing
        while to_build:
            new_item_needs = defaultdict(int)
            for item_name, qty_to_build in to_build.items():
                bp = next((b for b in blueprints if b.name == item_name), None)
                if not bp:
                    logger.warning("No blueprint found for intermediate item: %s", item_name)
                    continue
                produced[item_name] += qty_to_build
                accumulate_materials(bp, qty_to_build, total_needed, new_item_needs, blueprints)

            # Subtract inventory from the new layer of dependencies
            to_build = defaultdict(int)
            for name, needed_qty in new_item_needs.items():
                inv_qty = remaining_inventory.get(name, 0)
                used = min(inv_qty, needed_qty)
                if used > 0:
                    used_from_inv_total[name] += used
                    remaining_inventory[name] -= used
                if needed_qty > used:
                    to_build[name] = needed_qty - used

        # === Now build the top-level "what_to_produce" goals ===
        for b in blueprints:
            count = what_to_produce.get(b.name, 0)
            if count > 0:
                # Only accumulate materials if the blueprint has not been processed
                if b.name not in processed_blueprints:
                    final_produced[b.name] += count
                    accumulate_materials(b, count, total_needed, item_needs, blueprints)
                    processed_blueprints.add(b.name)  # Mark this blueprint as processed
                else:
                    # If already processed, just add to final_produced
                    final_produced[b.name] += count

        logger.info("Final produced items: %s", final_produced)  # Log final produced quantities



        # Satisfy needs from inventory first (for materials, not intermediates)
        inventory_cost_savings = 0.0
        inventory_items_used = {}

        # Create a copy of final_produced to preserve original numbers
        original_final_produced = dict(final_produced)
        adjusted_final_produced = {}

        for item_name, qty_needed in final_produced.items():
            adjusted_final_produced[item_name] = qty_needed  # Start with original required amount

            if qty_needed > 0:
                mat_obj = material_objs.get(item_name)

                if mat_obj:
                    inv_qty = remaining_inventory.get(item_name, 0)
                    if inv_qty > 0:
                        used_from_inv = min(inv_qty, qty_needed)

                        if used_from_inv > 0:
                            remaining_inventory[item_name] -= used_from_inv
                            category = getattr(mat_obj, "category", "Other")

                            inventory_items_used[item_name] = {
                                "amount": used_from_inv,
                                "category": category,
                                "original_required": qty_needed,  # Track original requirement
                                "remaining_requirement": qty_needed - used_from_inv  # Track what's left to produce
                            }

                            if hasattr(mat_obj, 'sell_price'):
                                inventory_cost_savings += used_from_inv * mat_obj.sell_price

                            # Reduce the production requirement
                            adjusted_final_produced[item_name] -= used_from_inv

        logger.info("Original production requirements: %s", original_final_produced)
        logger.info("Consumed from inventory: %s", inventory_items_used)
        logger.info("Actual production needed after inventory: %s", 
                   {k: v for k, v in adjusted_final_produced.items() if v > 0})






        
        # Calculate expected invention materials used and expected cost
        expected_invention_materials_used = defaultdict(float)
        invention_cost = 0.0 
        for b in blueprints:
            s_bp_name = sanitize_name(b.name)
            produced_qty = int(value(x[s_bp_name]) or 0)  # Get the solved quantity for this blueprint
            if produced_qty > 0:
                normalized_mats = normalize_materials_structure(b.materials) if isinstance(b.materials, list) else b.materials
                runs_per_copy = getattr(b, "runs_per_copy", 1)
                for section_name, section in normalized_mats.items():
                    if section_name == "Invention Materials":
                        for mat_name, qty_per_run in section.items():
                            s_mat_name = sanitize_name(mat_name)
                            # Calculate attempts needed (handle potential division by zero if invention_chance is 0 or None)
                            attempts_needed = 1.0  # Default to 1 if no invention chance (e.g., for T1 BPCs)
                            if hasattr(b, "invention_chance") and b.invention_chance is not None and b.invention_chance > 0:
                                attempts_needed = 1 / b.invention_chance
                            # Update expected invention materials used
                            expected_invention_materials_used[s_mat_name] += (qty_per_run * attempts_needed * produced_qty) / runs_per_copy
                            # Calculate expected cost for datacores
                            mat_obj = material_objs.get(mat_name)
                            if mat_obj and hasattr(mat_obj, 'sell_price'):
                                invention_cost += mat_obj.sell_price * (qty_per_run * attempts_needed * produced_qty) / runs_per_copy
        # Convert sanitized names back to original             
        report_invention_materials = {
            s_name_to_original.get(s_mat_name, s_mat_name): round(qty)  # Use .get for safety, round for display
            for s_mat_name, qty in expected_invention_materials_used.items()
            if qty > 0 
        }
        
        logger.debug("Expected invention materials used: %s", report_invention_materials)
                

        # Calculate final material usage (non-recursive)
        final_usage = defaultdict(float)

        # Accumulate materials for the total production goal
        for name, count in adjusted_final_produced.items():
            if count > 0:
                bp = next((bp for bp in blueprints if bp.name == name), None)
                if bp:
                    accumulate_materials(bp, count, final_usage, {}, blueprints)

        final_material_usage = {}
        all_materials = set(final_usage) | set(total_needed) | set(used_from_inv_total)
        for mat in all_materials:
            obj = material_objs.get(mat)
            starting_qty = getattr(obj, "quantity", inventory.get(mat, 0))
            category = getattr(obj, "category", "Other") if obj else "Other"

            used_int = int(round(final_usage.get(mat, 0)))
            final_material_usage[mat] = {
                "used": used_int,
                "remaining": starting_qty - used_int,
                "category": category
            }


        # Remaining dependencies after accounting for inventory
        deps = defaultdict(float)
        for b in blueprints:
            net_production = final_produced.get(b.name, 0)
            if net_production > 0:
                expand_materials(b, blueprints, quantity=net_production, t1_dependencies=deps, inventory=remaining_inventory)
        for name, inv_qty in untouched_inventory.items():
            if name in deps:
                used = min(inv_qty, deps[name])
                deps[name] -= used
                if deps[name] <= 0:
                    del deps[name]

        # Calculate profits
        total_sell = sum(bp.sell_price * what_to_produce.get(bp.name, 0) for bp in blueprints)
        # Calculate true profit considering material costs
        true_jita = 0.0
        for bp in blueprints:
            produced_qty = final_produced.get(bp.name, 0)
            if produced_qty > 0:
                # Calculate the total material cost for the produced quantity
                material_cost = (bp.full_material_cost if bp.tier == 'T2' else bp.material_cost)
                total_material_cost = material_cost * produced_qty

                # Log the values for debugging
                logger.info("Blueprint: %s, Produced: %d, Sell Price: %f, Material Cost: %f, Total Material Cost: %f",
                            bp.name, produced_qty, bp.sell_price, material_cost, total_material_cost)

                # Subtract the total material cost from the total sell price
                true_jita += (bp.sell_price * produced_qty) - total_material_cost
        logger.info("True Jita Profit: %f", true_jita)

        result = {
            "status": "Optimal",
            
            "total_profit": total_sell,
            "true_profit_jita": true_jita,
            "true_profit_inventory": true_jita + inventory_cost_savings,
            "inventory_cost_savings": inventory_cost_savings,
            "what_to_produce": what_to_produce,
            "original_production_plan": original_final_produced,
            "adjusted_production_plan": {k: v for k, v in adjusted_final_produced.items() if v > 0},
            "material_usage": final_material_usage,
            "dependencies_needed": {k: int(v) for k, v in deps.items() if v > 0},
            "inventory_savings": inventory_items_used,
            "expected_invention_materials_used": report_invention_materials,
            "invention_cost": invention_cost
        }

        logger.info("Optimization complete. Final result: %s", result)
        return jsonify(result), 200

    except Exception as e:
        logger.error("Error: %s", str(e))
        return jsonify({"error": "An error occurred during optimization"}), 500

