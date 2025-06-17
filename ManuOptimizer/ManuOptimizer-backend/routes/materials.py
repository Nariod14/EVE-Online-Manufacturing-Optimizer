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
from .utils import get_material_category_lookup, get_material_info, normalize_name
from models import BlueprintT2, db, Material
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
        data = request.json
        material = Material.query.get_or_404(id)

        material.quantity = data.get('quantity', material.quantity)
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


@materials_bp.route('/materials', methods=['POST'])
def add_material():
    try:
        data = request.form
        logger.info(f"Received material data: {data}")
        
        material = Material.query.filter_by(name=data['name']).first()
        if material:
            logger.info(f"Updating existing material: {data['name']}")
            material.quantity = data['quantity']
            material.type_id = data.get('type_id') or get_material_info(data['name'])['type_id']
            material.category = data.get('category') or get_material_info(data['name'])['category']
        else:
            logger.info(f"Adding new material: {data['name']}")
            new_material = Material(name=data['name'], quantity=data['quantity'], type_id=data.get('type_id'), category=data.get('category') or get_material_info(data['name'])['category'])
            db.session.add(new_material)
        
        db.session.commit()
        logger.info("Material added/updated successfully")
        return jsonify({"message": "Material updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding/updating material: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while adding/updating the material"}), 500

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
        sde_info = get_material_info(names)

        result = []
        for m in materials:
            sde_cat = sde_info.get(normalize_name(m.name), {}).get("category", "Other")
            result.append({
                "id": m.id,
                "name": m.name,
                "quantity": m.quantity,
                "type_id": m.type_id or sde_info.get(normalize_name(m.name), {}).get("type_id", None),
                "category": m.category or sde_cat
            })

        return jsonify(result), 200

    except Exception as e:
        logger.error("Error getting materials!\n" + traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while getting the materials"}), 500

    
@materials_bp.route('/update_materials', methods=['POST'])
def update_materials():
    try:
        data = request.json
        materials = data.get('materials', {})
        update_type = data.get('updateType', 'replace')

        logger.info(f"Received materials data: {materials}")
        logger.info(f"Update type: {update_type}")

        all_names = list(materials.keys())
        material_info = get_material_info(all_names)  # Dict[str, {"type_id": ..., "category": ...}]

        if update_type == 'replace':
            Material.query.delete()
            db.session.commit()
            logger.info("All existing materials have been deleted.")

        for name, quantity in materials.items():
            info = material_info.get(name, {})
            type_id = info.get("type_id", 0)
            category = info.get("category", "Other")

            existing_material = Material.query.filter_by(name=name).first()

            if update_type == 'add' and existing_material:
                logger.info(f"Updating material: {name} -> Qty: {quantity}, Cat: {category}, ID: {type_id}")
                existing_material.quantity = quantity
                existing_material.category = category
                existing_material.type_id = type_id
            else:
                logger.info(f"Adding new material: {name} -> Qty: {quantity}, Cat: {category}, ID: {type_id}")
                new_material = Material(name=name, quantity=quantity, category=category, type_id=type_id)
                db.session.add(new_material)

        db.session.commit()
        logger.info("Materials updated successfully.")
        return jsonify({"message": "Materials updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating materials: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while updating materials"}), 500
    

@materials_bp.route('/update_material_info', methods=['POST'])
def update_material_info():
    try:
        materials = Material.query.all()
        
        for material in materials:
            material_info = get_material_info([material.name])[material.name]
            material.type_id = material_info['type_id']
            material.category = material_info['category']
            logger.info(f"Updated material '{material.name}' (type_id: {material.type_id}, category: {material.category})")

        
        db.session.commit()
        logger.info("Material info updated successfully")
        return jsonify({"message": "Material info updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Error updating material info!\n" + traceback.format_exc())
        return jsonify({"ERROR": "An error occurred while updating the material info"}), 500