from collections import defaultdict
from flask import jsonify, render_template, request
import logging
import traceback
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from models import BlueprintT2, db, Blueprint, Material




logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


def expand_materials(bp, blueprints, quantity=1, t1_dependencies=None):
    expanded = defaultdict(float)
    for section_name, section in bp.materials.items():
        for mat, qty in section.items():
            sub_bp = next((b for b in blueprints if b.name == mat), None)
            if section_name == "Invention Materials" and hasattr(bp, "invention_chance") and bp.invention_chance and hasattr(bp, "runs_per_copy") and bp.runs_per_copy:
                attempts_needed = quantity / (bp.runs_per_copy * bp.invention_chance)
                expanded[mat] += qty * attempts_needed
            elif sub_bp:
                if getattr(sub_bp, "tier", "T1") == "T1":
                    # Log T1 dependency
                    if t1_dependencies is not None:
                        t1_dependencies[mat] = t1_dependencies.get(mat, 0) + qty * quantity
                    sub_mats = expand_materials(sub_bp, blueprints, qty * quantity, t1_dependencies)
                    for sm, sq in sub_mats.items():
                        expanded[sm] += sq
                else:
                    sub_mats = expand_materials(sub_bp, blueprints, qty * quantity, t1_dependencies)
                    for sm, sq in sub_mats.items():
                        expanded[sm] += sq
                    expanded[mat] += qty * quantity
            else:
                expanded[mat] += qty * quantity
    return expanded


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

# Add this helper function to routes.py
def create_esi_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount('https://', HTTPAdapter(max_retries=retry))
    return session

def fetch_jita_price(blueprint_name):
    session = create_esi_session()
    region_id = 10000002  # The Forge (Jita)
    location_id = 60003760  # Jita 4-4 station
    
    try:
        # Get type ID
        type_resp = session.post(
            "https://esi.evetech.net/latest/universe/ids/",
            json=[blueprint_name]
        )
        type_resp.raise_for_status()
        type_data = type_resp.json()
        
        if not type_data.get('inventory_types'):
            return None
            
        type_id = type_data['inventory_types'][0]['id']
        
        # Get market orders
        orders = []
        page = 1
        while True:
            orders_resp = session.get(
                f"https://esi.evetech.net/latest/markets/{region_id}/orders/",
                params={
                    'type_id': type_id,
                    'order_type': 'sell',
                    'page': page
                }
            )
            orders_resp.raise_for_status()
            page_orders = orders_resp.json()
            orders.extend(page_orders)
            
            if len(page_orders) < 1000:
                break
            page += 1
        
        # Filter Jita 4-4 orders and find lowest price
        jita_orders = [o for o in orders if o['location_id'] == location_id]
        if not jita_orders:
            return None
            
        return min(o['price'] for o in jita_orders)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"ESI request failed: {str(e)}")
        return None

# Price fetching updates
def fetch_market_price(blueprint_name, region_id, station_id=None, use_region=False):
    session = create_esi_session()
    try:
        # Validate station exists if provided
        if station_id and not use_region:
            station_resp = session.get(
                f"https://esi.evetech.net/latest/universe/stations/{station_id}/"
            )
            if station_resp.status_code != 200:
                return None

        # Get type ID (cached implementation recommended for production)
        type_resp = session.post(
            "https://esi.evetech.net/latest/universe/ids/",
            json=[blueprint_name]
        )
        type_resp.raise_for_status()
        type_data = type_resp.json()
        type_id = type_data['inventory_types'][0]['id']

        # Market orders query
        orders = []
        page = 1
        while True:
            params = {
                'type_id': type_id,
                'order_type': 'sell',
                'page': page
            }
            
            if use_region:
                endpoint = f"markets/{region_id}/orders/"
            else:
                endpoint = f"markets/structures/{station_id}/"

            orders_resp = session.get(
                f"https://esi.evetech.net/latest/{endpoint}",
                params=params
            )
            
            if orders_resp.status_code == 403:
                raise ValueError("Structure market access not allowed")
                
            orders_resp.raise_for_status()
            page_orders = orders_resp.json()
            orders.extend(page_orders)

            if len(page_orders) < 1000:
                break
            page += 1

        # Price determination logic
        if use_region:
            return min(o['price'] for o in orders if o['location_id'] == station_id) if station_id else min(o['price'] for o in orders)
        else:
            return min(o['price'] for o in orders) if orders else None

    except requests.exceptions.RequestException as e:
        logger.error(f"Market price fetch failed: {str(e)}")
        return None




