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

import pulp
from .utils import get_material_category_lookup
from models import BlueprintT2, db, Material
from flask import Blueprint
from pulp import LpProblem, LpVariable, lpSum, value, LpMaximize, LpStatus, PULP_CBC_CMD





materials_bp = Blueprint('materials', __name__,url_prefix='/api/materials')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


@materials_bp.route('/material/<int:id>', methods=['PUT'])
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


@materials_bp.route('/material', methods=['POST'])
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
    
@materials_bp.route('/material', methods=['GET'])
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
    
@materials_bp.route('/update_materials', methods=['POST'])
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

