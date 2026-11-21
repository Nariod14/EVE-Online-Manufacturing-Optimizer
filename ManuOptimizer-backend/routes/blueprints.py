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
from models import BlueprintT2, Blueprint as BlueprintModel, BuyListItem, Station, db, Material
from flask import Blueprint
from pulp import LpProblem, LpVariable, lpSum, value, LpMaximize, LpStatus, PULP_CBC_CMD, LpAffineExpression
from .optimizer_core import build_plan, split_materials
from .utils import get_item_volumes
from .buylist import refresh_buy_list_prices
from .market import DEFAULT_SUGGEST_DAYS, DEFAULT_WINDOW_DAYS, average_daily_volume, fetch_market_history, suggested_max





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


# ---------------------------------------------------------------------------
# Units convention
#   The database stores a blueprint's materials and material_cost PER RUN.
#   amt_per_run says how many units one run makes (reactions, charges: > 1).
#   GET /blueprints shows materials and material_cost PER UNIT (divided by
#   amt_per_run), so anything that comes back from the edit form is per unit
#   too and has to be scaled back up before it is stored.
# ---------------------------------------------------------------------------
def _clean_amt_per_run(value, default=1):
    """A whole number of units per run, never below 1."""
    try:
        value = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return value if value >= 1 else default


def _scale_quantity(quantity, factor):
    try:
        scaled = float(quantity) * factor
    except (TypeError, ValueError):
        return quantity
    nearest = round(scaled)
    if abs(scaled - nearest) < 1e-6:      # 98 / 160 * 160 comes back as 98, not 98.00000000000001
        return int(nearest)
    return round(scaled, 6)


def _materials_to_per_run(materials, amt_per_run):
    """Convert per-unit materials from the edit form back to the stored per-run form."""
    if not amt_per_run or amt_per_run == 1:
        return materials
    if isinstance(materials, list):
        converted = []
        for entry in materials:
            if isinstance(entry, dict) and "quantity" in entry:
                entry = {**entry, "quantity": _scale_quantity(entry["quantity"], amt_per_run)}
            converted.append(entry)
        return converted
    if isinstance(materials, dict):
        converted = {}
        for category, contents in materials.items():
            if isinstance(contents, dict):
                converted[category] = {name: _scale_quantity(qty, amt_per_run) for name, qty in contents.items()}
            else:
                converted[category] = _scale_quantity(contents, amt_per_run)
        return converted
    return materials


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
        amt_per_run = _clean_amt_per_run(data.get('amt_per_run', 1))
        runs_per_copy_raw = data.get('runs_per_copy')
        runs_per_copy = int(runs_per_copy_raw) if runs_per_copy_raw is not None else None

        headers = {'User-Agent': 'ManuOptimizer 1.0 nariod14@gmail.com'}

        category_lookup = get_material_category_lookup()
        normalized_materials, name, is_reaction = parse_blueprint_text(raw_blueprint_paste, category_lookup)

        # Override tier if it’s a reaction
        if is_reaction:
            blueprint_tier = "Reaction"

        # The pasted quantities are for one run and are stored that way (see the
        # units convention at the top of this file). amt_per_run is saved on the
        # blueprint; it must not be divided into the materials here, because
        # GET /blueprints already divides by it for display.

        logger.info(f"Parsed blueprint name: {name} (Reaction: {is_reaction})")

        # === Type ID lookup ===
        blueprint_info = get_item_info([name])
        typeID = blueprint_info.get(normalize_name(name), {}).get("type_id", 0)

        if not typeID:
            logger.warning(f"Blueprint name not found in SDE: {name}, unable to resolve typeID.")
            return jsonify({"error": f"Blueprint name not found in SDE: {name}"}), 400

        # === Sell price ===
        if sell_price == 0 or sell_price is None:
            sell_price = get_lowest_jita_sell_price(typeID, headers=headers)[0]

        # === Material cost calculation ===
        if not material_cost:
            material_names = [
                item_name
                for category in normalized_materials.values()
                for item_name in category.keys()
            ]
            material_info = get_item_info(material_names)
            type_id_map = {
                normalize_name(name): info["type_id"]
                for name, info in material_info.items()
            }
            type_ids = list(set(type_id_map.values()))
            price_map = get_lowest_jita_sell_prices_loop(type_ids, headers=headers)

            material_cost = 0
            for category, materials in normalized_materials.items():
                for mat_name, quantity in materials.items():
                    norm = normalize_name(mat_name)
                    tid = type_id_map.get(norm)
                    unit_price = price_map.get(tid, 0.0)
                    material_cost += quantity * unit_price

        # === T2 logic (unchanged) ===
        invention_materials_dict = {}
        invention_cost = 0
        full_material_cost = material_cost

        if blueprint_tier == "T2" and raw_invention_paste.strip():
            invention_materials_dict, invention_cost = parse_ingame_invention_text(raw_invention_paste)
            if invention_materials_dict:
                normalized_materials.setdefault("Invention Materials", {}).update(invention_materials_dict)

            if invention_chance and invention_chance > 1:
                invention_chance /= 100

            if invention_chance and invention_chance > 0:
                detected_invention_cost = invention_cost / (invention_chance * runs_per_copy)
            else:
                detected_invention_cost = 0

            full_material_cost = material_cost + detected_invention_cost

        # === Save/update logic ===
        if blueprint_tier == "T2":
            model = BlueprintT2
        else:
            model = BlueprintModel

        existing = model.query.filter_by(name=name).first()
        if existing:
            existing.type_id = typeID
            existing.materials = normalized_materials
            existing.sell_price = sell_price
            existing.material_cost = material_cost
            existing.tier = blueprint_tier
            existing.amt_per_run = amt_per_run
            if blueprint_tier == "T2":
                existing.full_material_cost = full_material_cost
                existing.invention_chance = invention_chance
                existing.invention_cost = invention_cost
                existing.runs_per_copy = runs_per_copy
            db.session.commit()
            return jsonify({
                "message": "Blueprint updated successfully",
                "is_reaction": is_reaction,
                "tier": blueprint_tier
            }), 200

        # New entry
        new_blueprint = model(
            name=name,
            type_id=typeID,
            materials=normalized_materials,
            sell_price=sell_price,
            material_cost=material_cost,
            tier=blueprint_tier,
            amt_per_run=amt_per_run
        )
        if blueprint_tier == "T2":
            new_blueprint.full_material_cost = full_material_cost
            new_blueprint.invention_chance = invention_chance
            new_blueprint.invention_cost = invention_cost
            new_blueprint.runs_per_copy = runs_per_copy

        db.session.add(new_blueprint)
        db.session.commit()

        logger.info(f"Blueprint: {name} (Reaction: {is_reaction}) added successfully")

        return jsonify({
            "message": "Blueprint added successfully",
            "is_reaction": is_reaction,
            "tier": blueprint_tier
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding blueprint! See traceback:")
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
        new_blueprint = BlueprintModel(
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
                "max": b.max,                  # units sold per plan; was missing, so the list always showed it blank
                "type_id": b.type_id,
                "region_id": b.region_id,
                "material_cost": b.material_cost / b.amt_per_run,
                "tier": b.tier,
                "station_id": b.station_id,
                "station_name": b.station.name if b.station else "Jita 4-4 Caldari Navy Assembly Plant",
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

        # What the form shows was divided by the amt_per_run the blueprint had when
        # it was loaded, so that is the factor that turns it back into per-run values.
        shown_amt_per_run = _clean_amt_per_run(blueprint.amt_per_run)

        if data.get('name'):
            blueprint.name = data['name']
        if data.get('materials') is not None:
            blueprint.materials = _materials_to_per_run(data['materials'], shown_amt_per_run)
        if data.get('sell_price') is not None:
            blueprint.sell_price = data['sell_price']
        if data.get('material_cost') is not None:
            blueprint.material_cost = float(data['material_cost']) * shown_amt_per_run
        if data.get('amt_per_run') is not None:
            blueprint.amt_per_run = _clean_amt_per_run(data['amt_per_run'], shown_amt_per_run)
        blueprint.max = data.get('max', blueprint.max)
        if data.get('tier'):
            blueprint.tier = data['tier']
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


@blueprints_bp.route('/blueprints/suggested_max', methods=['GET'])
def get_suggested_max():
    """Suggested max per blueprint from ESI market history.

    Query: days    suggested max = this many days of average daily volume (default 3)
           window  days of history to average over (default 30)
    """
    try:
        days = request.args.get('days', default=DEFAULT_SUGGEST_DAYS, type=float)
        window = request.args.get('window', default=DEFAULT_WINDOW_DAYS, type=int)
        if days is None or days < 0 or not window or window < 1 or window > 365:
            return jsonify({"error": "days must be >= 0 and window between 1 and 365"}), 400

        headers = {'User-Agent': 'ManuOptimizer 1.0'}
        blueprints = BlueprintModel.query.all()
        jobs = {}
        for bp in blueprints:
            if bp.type_id:
                jobs[bp.id] = (bp.region_id or 10000002, bp.type_id)

        histories = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_market_history, r, t, headers): (r, t) for r, t in set(jobs.values())}
            for future in concurrent.futures.as_completed(futures):
                histories[futures[future]] = future.result()

        result = []
        for bp in sorted(blueprints, key=lambda b: b.name):
            job = jobs.get(bp.id)
            avg = average_daily_volume(histories.get(job), window) if job else None
            result.append({
                "id": bp.id,
                "name": bp.name,
                "tier": bp.tier,
                "region_id": job[0] if job else None,
                "current_max": bp.max,
                "avg_daily_volume": None if avg is None else round(avg, 2),
                "suggested_max": suggested_max(avg, days),
            })
        return jsonify({"days": days, "window": window, "blueprints": result}), 200
    except Exception:
        logger.error("Error getting suggested max values!\n" + traceback.format_exc())
        return jsonify({"error": "An error occurred while getting suggested max values"}), 500


@blueprints_bp.route('/blueprints/set_max', methods=['POST'])
def set_blueprint_max():
    """Set max on several blueprints at once. Body: {"max": {"<id>": 120, "<id>": null}}."""
    try:
        data = request.get_json(silent=True) or {}
        values = data.get("max")
        if not isinstance(values, dict):
            return jsonify({"error": "Expected {\"max\": {id: value}}"}), 400
        cleaned = {}
        for key, val in values.items():
            try:
                bp_id = int(key)
                cleaned[bp_id] = None if val is None else max(0, int(val))
            except (TypeError, ValueError):
                return jsonify({"error": f"Bad entry: {key}: {val}"}), 400
        updated = 0
        for bp in BlueprintModel.query.filter(BlueprintModel.id.in_(list(cleaned))).all():
            bp.max = cleaned[bp.id]
            updated += 1
        db.session.commit()
        return jsonify({"message": f"Max updated on {updated} blueprint(s)", "updated": updated}), 200
    except Exception:
        db.session.rollback()
        logger.error("Error setting max values!\n" + traceback.format_exc())
        return jsonify({"error": "An error occurred while setting max values"}), 500


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
                # Keep the last known price: sell_price is NOT NULL, and setting it to
                # None made the whole price update fail and roll back.
                logger.warning(f"No price found for blueprint {bp.name} (type_id: {bp.type_id}); keeping the previous sell price")
                bp.used_jita_fallback = False


        # Material cost per run. This used to sit inside the loop above, so every
        # blueprint's cost was recomputed once per blueprint (same result, N times over).
        name_to_type_id = existing_name_to_id
        type_id_to_price = {
            tid: prices.get(tid, (None,))[0]
            for tid in name_to_type_id.values()
            if tid is not None
        }

        for bp in blueprints:
            total_cost = 0.0
            invention_cost = 0.0

            normalized = bp.get_normalized_materials()
            missing_material_price = False

            for category, materials_dict in normalized.items():
                for mat_name, qty in materials_dict.items():
                    type_id = name_to_type_id.get(mat_name)
                    unit_price = type_id_to_price.get(type_id)

                    if unit_price is None:
                        logger.warning(f"No price for material {mat_name} (type_id: {type_id}) in blueprint {bp.name}")
                        if category != "Invention Materials":
                            missing_material_price = True
                        continue

                    if category == "Invention Materials":
                        invention_cost += unit_price * qty
                    else:
                        total_cost += unit_price * qty

            if missing_material_price:
                # A cost with an input left out would be too low and make the
                # blueprint look more profitable than it is, so keep the old one.
                logger.warning(f"Keeping the previous material cost for {bp.name}: at least one input has no price")
            else:
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



        # Buy-list items may not be in inventory, so they are priced separately.
        # fetch_price caches by type_id, so items also in inventory cost no extra request.
        buy_list_items = BuyListItem.query.all()
        if buy_list_items:
            no_price = refresh_buy_list_prices(buy_list_items, headers)
            if no_price:
                logger.warning(f"No price for buy-list items: {no_price}")

        db.session.commit()
        return jsonify({"message": "Prices updated successfully"}), 200

    except Exception:
        db.session.rollback()
        logger.error("Error updating prices", exc_info=True)
        return jsonify({"error": "An error occurred while updating prices"}), 500





@blueprints_bp.route('/optimize', methods=['GET'])
def optimize():
    """Most profitable production plan for the current inventory.

    Optional query parameters (without them it is "inventory only", as before):
        budget  ISK available for buying materials, e.g. ?budget=200000000
        buy     "list" (default when a budget is given: only what is on the buy list,
                see routes/buylist.py), "all" or "none". "minerals" is read as "list".
        fee     sales tax + broker fee, as a fraction (0.05) or a percentage (5)
        cargo   m3 (capacity x trips) that everything bought, and separately everything
                sold, must fit in, e.g. ?cargo=125000
        cargo_buy / cargo_sell   0 to switch that side of the limit off (default 1)

    The solver itself lives in routes/optimizer_core.py.
    """
    try:
        blueprints = BlueprintModel.query.all()
        materials = Material.query.all()

        if not blueprints or not materials:
            return jsonify({"status": "No optimal solution found"}), 400

        budget = request.args.get('budget', default=0.0, type=float) or 0.0
        fee = request.args.get('fee', default=0.0, type=float) or 0.0
        buy_mode = (request.args.get('buy') or ('list' if budget > 0 else 'none')).lower()
        buy_list = {i.name: i.sell_price for i in BuyListItem.query.all()}
        # cargo: m3 everything bought must fit in (hauler capacity x trips); 0 = no limit
        cargo_m3 = request.args.get('cargo', default=0.0, type=float) or 0.0
        # each side of the limit can be switched off to compare plans (default on)
        cargo_buy = request.args.get('cargo_buy', default='1') not in ('0', 'false', 'off')
        cargo_sell = request.args.get('cargo_sell', default='1') not in ('0', 'false', 'off')
        # m3 per unit of everything that can be bought or sold: the cargo limit, and the
        # shopping list's and sales' volume (shown even without a limit)
        names = {m.name for m in materials} | set(buy_list) | {b.name for b in blueprints}
        for b in blueprints:
            names.update(split_materials(b.materials)[0])
        volumes = get_item_volumes(names)

        logger.info("Materials loaded: %s", {m.name: m.quantity for m in materials})
        logger.info("Solving optimization problem (budget=%s, fee=%s, buy=%s, cargo=%s m3, on buys=%s, on sales=%s)...",
                    budget, fee, buy_mode, cargo_m3, cargo_buy, cargo_sell)

        result, status_code = build_plan(
            blueprints,
            materials,
            budget=budget,
            fee=fee,
            buy_mode=buy_mode,
            buy_list=buy_list,
            volumes=volumes,
            cargo_m3=cargo_m3,
            cargo_buy=cargo_buy,
            cargo_sell=cargo_sell,
            debug_lp_path="lp_debug_output.lp",
        )

        if status_code != 200:
            logger.info("Optimization failed: %s", result)
            return jsonify(result), status_code

        logger.info("Optimal production (runs): %s", result["what_to_produce"])
        logger.info("Units to sell: %s", result["units_sold"])
        logger.info("Build first: %s", result["dependencies_needed"])
        logger.info("Sell value: %.2f, true profit: %.2f", result["total_revenue"], result["true_profit"])
        if result["shopping_list"]:
            logger.info("Shopping list: %s", result["shopping_list"])
        for warning in result["warnings"]:
            logger.warning("Optimizer: %s", warning)
        logger.info("Optimization complete. Final result: %s", result)
        return jsonify(result), 200

    except Exception as e:
        logger.error("Error: %s", str(e))
        logger.error(traceback.format_exc())
        return jsonify({"error": "An error occurred during optimization"}), 500
