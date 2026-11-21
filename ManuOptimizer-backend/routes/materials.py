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
from flask import Blueprint
from .utils import get_material_category_lookup, get_item_info, normalize_name, resolve_item_names, search_items
from .optimizer_core import split_materials
from models import Blueprint as BlueprintModel, BlueprintT2, db, Material
from flask import Blueprint

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

materials_bp = Blueprint('materials', __name__,url_prefix='/api/materials')
@materials_bp.route('/material/<int:id>', methods=['PUT'])
def update_material(id):
    try:
        data = request.get_json(silent=True) or {}
        material = db.session.get(Material, id)
        if material is None:
            return jsonify({"error": "Material not found"}), 404

        if 'quantity' in data:
            quantity = _parse_quantity(data['quantity'])
            if quantity is None:
                return jsonify({"error": "Quantity must be a whole number, 0 or more"}), 400
            material.quantity = quantity
        material.type_id = data.get('type_id', material.type_id)
        material.category = data.get('category', material.category or "Other")

        db.session.commit()
        logger.info("Material updated successfully")
        return jsonify({"message": "Material updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error("Error updating material!\n" + traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while updating the material"}), 500


@materials_bp.route('/material/<int:id>', methods=['DELETE'])
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


def _parse_quantity(value):
    """A whole, non-negative quantity, or None if it is not one.

    Accepts numbers and the strings the game copies ("1,234", "1 234", "1.234"
    with a thousands separator). A decimal like "12.5" is rejected, not rounded.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        return int(value) if value >= 0 and value.is_integer() else None
    if isinstance(value, str):
        text = re.sub(r"[\s,'  ]", "", value)
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", text):   # 1.234.567 = thousands separators
            text = text.replace(".", "")
        if text.isdigit():
            return int(text)
    return None


def _serialize_material(m):
    return {
        "id": m.id,
        "name": m.name,
        "quantity": m.quantity,
        "type_id": m.type_id,
        "category": m.category,
        "sell_price": m.sell_price,
    }


@materials_bp.route('/search', methods=['GET'])
def search_material_names():
    """Marketable items matching ?q= (at least 2 characters), for the add box."""
    try:
        q = request.args.get('q', '')
        limit = request.args.get('limit', default=20, type=int) or 20
        return jsonify(search_items(q, limit)), 200
    except Exception:
        logger.error("Error searching items!\n" + traceback.format_exc())
        return jsonify({"error": "An error occurred while searching items"}), 500


@materials_bp.route('/materials', methods=['POST'])
def add_material():
    """Add one item, or set the quantity of one you already have.

    Body (JSON, or a form for older callers): {"name": "Morphite", "quantity": 5000,
    "mode": "set" | "add"}. "set" (default) replaces the quantity, "add" adds to it.
    The name must be a real item; it is stored with the game's spelling.
    """
    try:
        data = request.get_json(silent=True) or request.form or {}
        name = data.get('name')
        quantity = _parse_quantity(data.get('quantity'))
        mode = data.get('mode') or 'set'
        if not isinstance(name, str) or not name.strip():
            return jsonify({"error": "Name is required"}), 400
        if quantity is None:
            return jsonify({"error": "Quantity must be a whole number, 0 or more"}), 400
        if mode not in ('set', 'add'):
            return jsonify({"error": "mode must be 'set' or 'add'"}), 400

        found, unknown = resolve_item_names([name])
        if unknown:
            return jsonify({"error": f"No item called '{normalize_name(name)}' exists", "unknown": unknown}), 400
        info = next(iter(found.values()))

        material = Material.query.filter_by(name=info["name"]).first()
        if material:
            material.quantity = (material.quantity or 0) + quantity if mode == 'add' else quantity
            material.type_id = info["type_id"]
            material.category = material.category or info["category"]
            created = False
        else:
            material = Material(name=info["name"], quantity=quantity,
                                type_id=info["type_id"], category=info["category"])
            db.session.add(material)
            created = True

        db.session.commit()
        logger.info(f"Material {'added' if created else 'updated'}: {material.name} = {material.quantity}")
        return jsonify({"message": f"{material.name}: {material.quantity:,}", "created": created,
                        "material": _serialize_material(material)}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding/updating material: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while adding/updating the material"}), 500


@materials_bp.route('/add_missing_inputs', methods=['POST'])
def add_missing_inputs():
    """Add every blueprint input you have no row for yet, at quantity 0.

    Items you build yourself are skipped. Returns the names added.
    """
    try:
        blueprints = BlueprintModel.query.all()
        built = {b.name for b in blueprints}
        have = {m.name for m in Material.query.all()}
        wanted = set()
        for b in blueprints:
            inputs, invention, _ = split_materials(b.materials)
            wanted.update(inputs)
            wanted.update(invention)
        wanted = sorted(n for n in wanted if n not in built and n not in have)

        found, unknown = resolve_item_names(wanted)
        added = []
        for n in wanted:
            info = found.get(n)
            if not info or info["name"] in have:
                continue
            db.session.add(Material(name=info["name"], quantity=0,
                                    type_id=info["type_id"], category=info["category"]))
            have.add(info["name"])
            added.append(info["name"])
        db.session.commit()
        return jsonify({"added": added, "unknown": unknown}), 200
    except Exception:
        db.session.rollback()
        logger.error("Error adding missing inputs!\n" + traceback.format_exc())
        return jsonify({"error": "An error occurred while adding missing inputs"}), 500

@materials_bp.route('/material/<int:id>', methods=['GET'])
def get_material(id):
    try:
        material = Material.query.get_or_404(id)
        logger.info(f"Material {material.name} retrieved successfully")
        return jsonify({
            "id": material.id,
            "name": material.name,
            "quantity": material.quantity,
            "type_id": material.type_id or None,
            "category": material.category
        }), 200
    except Exception as e:
        logger.error("Error getting material by ID!\n" + traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while retrieving the material"}), 500

    
@materials_bp.route('/materials', methods=['GET'])
def get_materials():
    try:
        materials = Material.query.all()
        logger.info("Materials retrieved successfully")

        # Use SDE-based info for fallback category lookup
        names = [m.name for m in materials]
        sde_info = get_item_info(names)

        result = []
        for m in materials:
            sde_cat = sde_info.get(normalize_name(m.name), {}).get("category", "Other")
            result.append({
                "id": m.id,
                "name": m.name,
                "quantity": m.quantity,
                "type_id": m.type_id or sde_info.get(normalize_name(m.name), {}).get("type_id", None),
                "category": m.category or sde_cat,
                "sell_price": m.sell_price,
            })

        return jsonify(result), 200

    except Exception as e:
        logger.error("Error getting materials!\n" + traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while getting the materials"}), 500

    
@materials_bp.route('/update_materials', methods=['POST'])
def update_materials():
    """Paste import. Body: {"materials": {name: quantity}, "updateType": "add" | "replace"}.

    add      set the quantity of each pasted item (others are kept)
    replace  the paste becomes the whole inventory
    Every name must be a real item and every quantity a whole number >= 0;
    otherwise nothing is changed and the problems are returned.
    """
    try:
        data = request.get_json(silent=True) or {}
        materials = data.get('materials', {})
        update_type = data.get('updateType', 'replace')
        if not isinstance(materials, dict) or not materials:
            return jsonify({"error": "Nothing to import"}), 400
        if update_type not in ('add', 'replace'):
            return jsonify({"error": "updateType must be 'add' or 'replace'"}), 400

        logger.info(f"Received materials data: {materials}")
        logger.info(f"Update type: {update_type}")

        bad_quantity = []
        totals = {}                          # SDE name -> quantity (same item twice is summed)
        found, unknown = resolve_item_names(list(materials.keys()))
        for raw_name, raw_qty in materials.items():
            qty = _parse_quantity(raw_qty)
            if qty is None:
                bad_quantity.append(f"{raw_name}: {raw_qty}")
                continue
            info = found.get(normalize_name(raw_name)) if isinstance(raw_name, str) else None
            if info:
                totals[info["name"]] = totals.get(info["name"], 0) + qty

        if unknown or bad_quantity:
            parts = []
            if unknown:
                parts.append("Unknown items: " + ", ".join(unknown))
            if bad_quantity:
                parts.append("Bad quantities: " + ", ".join(bad_quantity))
            return jsonify({"error": ". ".join(parts) + ". Nothing was changed.",
                            "unknown": unknown, "bad_quantity": bad_quantity}), 400

        info_by_name = {i["name"]: i for i in found.values()}
        if update_type == 'replace':
            Material.query.delete()          # same transaction: a failure below keeps the old inventory
            existing = {}
        else:
            existing = {m.name: m for m in Material.query.all()}

        for name, quantity in totals.items():
            info = info_by_name[name]
            material = existing.get(name)
            if material:
                material.quantity = quantity
                material.type_id = info["type_id"]
                material.category = info["category"]
            else:
                db.session.add(Material(name=name, quantity=quantity,
                                        category=info["category"], type_id=info["type_id"]))

        db.session.commit()
        logger.info(f"Materials updated successfully ({len(totals)} items, {update_type}).")
        return jsonify({"message": f"{len(totals)} item(s) imported", "count": len(totals)}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating materials: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while updating materials"}), 500
    

@materials_bp.route('/update_material_info', methods=['POST'])
def update_material_info():
    try:
        materials = Material.query.all()
        found, unknown = resolve_item_names([m.name for m in materials])

        for material in materials:
            info = found.get(normalize_name(material.name))
            if not info:
                # Keep what is stored rather than overwriting it with type_id 0 / "Other"
                logger.warning(f"No item called '{material.name}' in the SDE; left unchanged")
                continue
            material.type_id = info['type_id']
            material.category = info['category']
            logger.info(f"Updated material '{material.name}' (type_id: {material.type_id}, category: {material.category})")

        if unknown:
            db.session.commit()
            return jsonify({"message": f"Material info updated. Not found in the SDE: {', '.join(unknown)}"}), 200

        db.session.commit()
        logger.info("Material info updated successfully")
        return jsonify({"message": "Material info updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Error updating material info!\n" + traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while updating the material info"}), 500