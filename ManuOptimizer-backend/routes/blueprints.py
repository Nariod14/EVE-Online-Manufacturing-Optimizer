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
from .utils import compute_expanded_materials, expand_materials, expand_sub_blueprints_one_level, fetch_price, get_lowest_jita_sell_price, get_lowest_jita_sell_prices_loop, get_material_category_lookup, get_item_info, get_material_quantity, normalize_materials_structure, normalize_name, parse_blueprint_text, parse_ingame_invention_text, refresh_access_token, safe_subtract, validate_inventory
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
                        "quantity": quantity,
                        "category": category
                    })
            bp_dict = {
                "id": b.id,
                "name": b.name,
                "materials": materials,
                "sell_price": b.sell_price,
                "amt_per_run": b.amt_per_run,
                "material_cost": b.material_cost,
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

        unique_type_ids = set()
        material_jobs = []
        blueprint_jobs = []

        # Stage material fetch jobs (always Jita)
        for mat in materials:
            if mat.type_id:
                unique_type_ids.add(mat.type_id)
                material_jobs.append((mat.type_id, None))

        # Stage blueprint fetch jobs
        for bp in blueprints:
            if not bp.type_id:
                info = get_item_info([bp.name])
                logger.debug(f"Lookup result for '{bp.name}': {info}")
                bp.type_id = info[normalize_name(bp.name)]['type_id']
            else:
                unique_type_ids.add(bp.type_id)
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

            name_to_type_id = {mat.name: mat.type_id for mat in materials}
            type_id_to_price = {mat.type_id: prices.get(mat.type_id, (None,))[0] for mat in materials}
            
            for bp in blueprints:
                total_cost = 0.0
                invention_cost = 0.0

                name_to_type_id = {mat.name: mat.type_id for mat in materials}
                type_id_to_price = {mat.type_id: prices.get(mat.type_id, (None,))[0] for mat in materials}

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

        if not blueprints or not inventory:
            return jsonify({"status": "No optimal solution found"}), 400

        logger.info("Materials loaded: %s", inventory)

        bp_names = {b.name for b in blueprints}
        profit_per_bp = {
            b.name: (b.sell_price - (b.full_material_cost if b.tier == 'T2' else b.material_cost) / b.amt_per_run)
            for b in blueprints
        }
        
        logger.info("Profits per blueprint: %s", profit_per_bp)
        
        result, final_usage = {}, defaultdict(float)
        final_produced = defaultdict(int)

        iteration = 0
        used_from_inv_total = defaultdict(int)
        final_produced = defaultdict(int)
        while True:
            iteration += 1
            logger.info("\n--- Iteration %d ---", iteration)
            logger.info("Inventory at start: %s", inventory)
            validate_inventory(inventory, iteration)

            # Step 1: maximize profit based on current inventory
            x = {b.name: LpVariable(f"x_{b.name}_{iteration}", lowBound=0, cat='Integer') for b in blueprints}
            prob1 = LpProblem(f"MaxProfit_{iteration}", LpMaximize)
            prob1 += lpSum(profit_per_bp[b.name] * x[b.name] for b in blueprints)

            usage = defaultdict(LpAffineExpression)
            for b in blueprints:
                quantity = getattr(b, "amt_per_run", 1)
                expanded = expand_materials(b, blueprints, quantity=quantity, inventory=inventory)
                if "Simple Asteroid Mining Crystal Type B I" in expanded:
                    logger.debug(f"[Iter {iteration}][Step1] Blueprint {b.name} expanded usage for Simple Asteroid Mining Crystal Type B I: {expanded['Simple Asteroid Mining Crystal Type B I'] * x[b.name]}")
                for mat, amt in expanded.items():
                    usage[mat] += amt * x[b.name]

            base_materials = set(inventory.keys()) - bp_names

            for mat in base_materials:
                prob1 += usage[mat] <= inventory[mat]

            for b in blueprints:
                if b.max is not None:
                    prob1 += x[b.name] <= b.max

            logger.info("Solving Step 1 (maximize profit)...")
            prob1.solve(PULP_CBC_CMD(msg=False))

            if LpStatus[prob1.status] != 'Optimal':
                logger.info("Step 1 status: %s", LpStatus[prob1.status])
                break

            produced = {b.name: int(value(x[b.name]) or 0) for b in blueprints}
            logger.info("Step 1 produced: %s", produced)
            logger.info("Step 1 objective: %s", value(prob1.objective))
            
            


            # Step 2: Use items from inventory directly (consume inventory items instead of producing)
            used_from_inv = defaultdict(int)

            for b in blueprints:
                count = produced.get(b.name, 0)
                if count <= 0:
                    continue

                available = inventory.get(b.name, 0)
                used = min(count, available)

                if used > 0:
                    # Reduce production count before subtracting from inventory
                    produced[b.name] = count - used

                    # Add refunded base mats back to inventory for the used quantity
                    refunded = expand_materials(b, blueprints, quantity=used, inventory=inventory)
                    if "Simple Asteroid Mining Crystal Type B I" in refunded:
                        logger.debug(f"[Iter {iteration}][Refund] Refund from using inventory {used} x {b.name} includes Simple Asteroid Mining Crystal Type B I: {refunded['Simple Asteroid Mining Crystal Type B I']}")

                    for mat, amt in refunded.items():
                        inventory[mat] = inventory.get(mat, 0) + amt

                    # Now subtract used blueprint count from inventory safely
                    safe_subtract(inventory, b.name, used)

                    used_from_inv[b.name] += used
                    used_from_inv_total[b.name] += used

                    logger.info("Force-used %d x %s from inventory and refunded base mats: %s", used, b.name, refunded)

            # Remove zero production after using inventory; if none left, end loop
            produced = {k: v for k, v in produced.items() if v > 0}
            if not produced:
                logger.info("All production fulfilled by inventory. Ending loop.")
                break

            # Step 2.5: Subtract intermediate T2 components from inventory, refund base mats
            sub_component_usage = defaultdict(float)
            for b in blueprints:
                if b.tier == "T2":
                    count = produced.get(b.name, 0)
                    if count <= 0:
                        continue
                    mats = expand_sub_blueprints_one_level(b, blueprints, quantity=count)
                    for mat, needed_qty in mats.items():
                        available = inventory.get(mat, 0)
                        used = min(available, needed_qty)
                        if used > 0:
                            sub_blueprint = next((bp for bp in blueprints if bp.name == mat), None)
                            if sub_blueprint:
                                refund = expand_materials(sub_blueprint, blueprints, quantity=used, inventory=inventory)

                                for rmat, ramt in refund.items():
                                    inventory[rmat] = inventory.get(rmat, 0) + ramt
                                logger.debug(f"Inventory before sub-component use of {used} {mat}: {inventory.get(mat,0)}")
                                safe_subtract(inventory, mat, used)
                                logger.debug(f"Inventory after sub-component use of {used} {mat}: {inventory.get(mat,0)}")
                                sub_component_usage[mat] += used
                                logger.info(f"Sub-used {used} x {mat} (needed for {b.name}) and refunded: {refund}")
                                used_from_inv_total[mat] += used

            # Step 3: Reoptimize with updated inventory after refunds
            
            logger.info("Inventory before Step 3 optimization: %s", inventory)

            x2 = {b.name: LpVariable(f"x2_{b.name}_{iteration}", lowBound=0, cat='Integer') for b in blueprints}
            prob2 = LpProblem(f"Reoptimize_{iteration}", LpMaximize)
            
            for b in blueprints:
                if b.max is not None:
                    prob2 += x2[b.name] + final_produced.get(b.name, 0) <= b.max

            total_usage = defaultdict(LpAffineExpression)

            for b in blueprints:
                mats = expand_materials(b, blueprints, quantity=1)
                for mat, amt in mats.items():
                    total_usage[mat] += amt * x2[b.name]

            for mat in base_materials:
                prob2 += total_usage[mat] <= inventory[mat]

            prob2 += lpSum(profit_per_bp[b.name] * x2[b.name] for b in blueprints)

            logger.info("Solving Step 2 (reoptimize with refunded mats)...")
            prob2.solve(PULP_CBC_CMD(msg=False))
            logger.info("Step 2 status: %s", LpStatus[prob2.status])

            if LpStatus[prob2.status] != 'Optimal':
                break

            new_produced = {}

            # NEW: Accumulate Step 3 production only
            for b in blueprints:
                count = int(value(x2[b.name]) or 0)
                used = used_from_inv[b.name]  # already fulfilled in Step 2

                if count > 0 or used > 0:
                    new_produced[b.name] = count
                    final_produced[b.name] += count + used  # Step1 + Step2 (inv) + Step3

            logger.info("Inventory after Step 3 optimization: %s", inventory)
            logger.info("Delta produced: %s", new_produced)
            
            if not new_produced:
                logger.info("No new production in this iteration. Optimization complete.")
                break

            # Compute Step 3-only usage
            usage_totals = defaultdict(float)

            for b in blueprints:
                count = new_produced.get(b.name, 0)  # ONLY new production
                if count > 0:
                    for mat, amt in compute_expanded_materials(b, count, blueprints).items():
                        usage_totals[mat] += amt
                        if mat == "Simple Asteroid Mining Crystal Type B I":
                            logger.debug(f"[Iter {iteration}][Step3] Counting usage for Simple Asteroid Mining Crystal Type B I from {b.name}: {amt}  new produced count {count} difference = {amt - count}")

            # Now subtract used materials, respecting sub-component usage
            for mat, amt in usage_totals.items():
                already_sub_used = sub_component_usage.get(mat, 0)
                if amt <= already_sub_used:
                    logger.debug(f"Skipping subtracting {mat} from final usage because already sub-used")
                    continue

                subtract_amt = amt - already_sub_used
                safe_subtract(inventory, mat, subtract_amt)
                if mat == "Simple Asteroid Mining Crystal Type B I":
                    logger.debug(f"[Iter {iteration}][Inventory Subtract] Subtracting {subtract_amt} of Simple Asteroid Mining Crystal Type B I from inventory")

                logger.debug(f"Subtracted {subtract_amt} of {mat} from inventory after sub-component adjustments")

            logger.info("Produced quantities: %s", final_produced)
            logger.info("Material usage totals: %s", usage_totals)

            final_usage = usage_totals
            if "Simple Asteroid Mining Crystal Type B I" in usage_totals:
                logger.debug(f"[Iter {iteration}][Final Usage] Total usage so far: {usage_totals['Simple Asteroid Mining Crystal Type B I']}")

            logger.info("Final inventory: %s", inventory)
            logger.info("Final produced: %s", final_produced)
            logger.info("Final used from inv total: %s", used_from_inv_total)

            validate_inventory(inventory, iteration)

            #Avoid float precision issues
            for mat in inventory:
                inventory[mat] = max(0, int(round(inventory[mat])))



        if not final_produced:
            return jsonify({"status": "No optimal solution found in iterative optimization"}), 400
        final_material_usage = {}
        for mat, qty in material_objs.items():
            try:
                raw_used = final_usage.get(mat, 0)
                inv_used = used_from_inv_total.get(mat, 0)
                sub_used = sub_component_usage.get(mat, 0)
                used = max(0, raw_used - inv_used - sub_used)
                used_int = int(round(used))
                starting_qty = getattr(qty, "quantity", 0)
                final_material_usage[mat] = {
                    "used": used_int,
                    "remaining": starting_qty - used_int,
                    "category": getattr(qty, "category", "Other")
                }
            except Exception as e:
                logger.error(f"Error processing material {mat} (type {type(mat)}): {e}")
                raise


        
        # Calculate total value of items pulled from inventory directly
        inventory_usage_value = sum(
            used_from_inv_total[b.name] * b.sell_price
            for b in blueprints
            if used_from_inv_total.get(b.name, 0) > 0
        )
        
        # Check if any materials were over-refunded
        for mat in base_materials:
            material = material_objs.get(mat)
            if material is None:
                logger.warning(f"Material {mat} not found in material_objs during overspent check.")
                continue

            mat_quantity = getattr(material, "quantity", 0)
            inv_quantity = inventory.get(mat, 0)

            used = mat_quantity - inv_quantity

            if used < 0:
                logger.warning(f"Material {mat} over-refunded? Net used = {used}")
            elif used > mat_quantity:
                logger.error(f"Material {mat} OVERSPENT! Used {used} > available {mat_quantity}")




        # Calculate dependencies
        deps = defaultdict(float)

        for b in blueprints:
            count = final_produced.get(b.name, 0)

            # Subtract the items used directly from inventory for this blueprint
            used_from_inv = used_from_inv_total.get(b.name, 0)
            net_count = count - used_from_inv

            if net_count > 0:
                expand_materials(b, blueprints, quantity=net_count, t1_dependencies=deps, inventory=inventory)

        # Final pass to subtract any remaining inventory from dependencies
        for name, inv_qty in inventory.items():
            if name == "Simple Asteroid Mining Crystal Type B I":
                logger.info(f"Inventory qty for {name} is {inv_qty}")
            if name in deps:
                used = min(inv_qty, deps[name])
                deps[name] -= used
                if deps[name] <= 0:
                    del deps[name]

        logger.info("Final produced: %s", final_produced)
        logger.info("Used from inv total: %s", used_from_inv_total)
        logger.info("Final dependencies: %s", deps)


                
        
        
        # Calculate inventory savings
        inventory_savings = defaultdict(float)

        # Include materials saved by blueprints used from inventory (as you already have)
        for bp in blueprints:
            used_from_inventory = used_from_inv_total.get(bp.name, 0)
            if used_from_inventory > 0:
                mats_saved = expand_materials(bp, blueprints, quantity=used_from_inventory, inventory=inventory)
                for mat, amt in mats_saved.items():
                    inventory_savings[mat] += amt

        # Also include the blueprint items themselves pulled from inventory
        for item_name, qty_used in used_from_inv_total.items():
            inventory_savings[item_name] += qty_used


        total_sell = sum(bp.sell_price * final_produced.get(bp.name, 0) for bp in blueprints)
        true_jita = sum((bp.sell_price - bp.material_cost) * final_produced.get(bp.name, 0) for bp in blueprints)

        result = {
            "status": "Optimal",
            "total_profit": total_sell,
            "true_profit_jita": true_jita,
            "true_profit_inventory": true_jita + inventory_usage_value,
            "what_to_produce": final_produced,
            "material_usage": final_material_usage,
            "dependencies_needed": {
                k: int(v - inventory_savings.get(k, 0))
                for k, v in deps.items()
                if (v - inventory_savings.get(k, 0)) > 0
            },
            "inventory_savings": {
                mat: {
                    "amount": amt,
                    "category": getattr(material_objs.get(mat), "category", "Other")
                }
                for mat, amt in inventory_savings.items()
            }

        }

        logger.info("Optimization complete. Final result: %s", result)
        return jsonify(result), 200

    except Exception as e:
        logger.error("Error: %s", str(e))
        return jsonify({"error": "An error occurred during optimization"}), 500

