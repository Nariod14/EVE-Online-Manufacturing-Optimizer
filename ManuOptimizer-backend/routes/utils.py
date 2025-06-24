from collections import defaultdict
from functools import wraps
from flask import jsonify, render_template, request, session
import logging
import traceback
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import sys
import sqlite3
import unicodedata
from time import time

from models import BlueprintT2, db, Blueprint, Material


# Constants
JITA_REGION_ID = 10000002  # The Forge
JITA_STATION_ID = 60003760  # Caldari Navy Assembly Plant
CLIENT_ID = os.getenv("EVE_CLIENT_ID")
CLIENT_SECRET = os.getenv("EVE_CLIENT_SECRET")
TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"
PRICE_CACHE_TTL = 600  # seconds = 10 minutes



logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)



def normalize_name(name: str) -> str:
    return unicodedata.normalize("NFKC", name.strip())

def expand_materials(bp, blueprints, quantity=1, t1_dependencies=None):
    expanded = defaultdict(float)

    # Normalize materials if needed
    if isinstance(bp.materials, list):
        normalized = normalize_materials_structure(bp.materials)
    else:
        normalized = bp.materials

    for section_name, section in normalized.items():
        for mat, qty in section.items():
            sub_bp = next((b for b in blueprints if b.name == mat), None)

            if section_name == "Invention Materials" and hasattr(bp, "invention_chance") and bp.invention_chance and hasattr(bp, "runs_per_copy") and bp.runs_per_copy:
                attempts_needed = quantity / (bp.runs_per_copy * bp.invention_chance)
                expanded[mat] += qty * attempts_needed

            elif sub_bp:
                if getattr(sub_bp, "tier", "T1") == "T1":
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



def normalize_materials_structure(materials_raw):
    """
    Ensures materials are in the nested dict format:
    {
    "Minerals": {
        "Tritanium": 100,
        "Pyerite": 50
    },
    ...
    }
    """
    if isinstance(materials_raw, dict):
        return materials_raw  # Already in correct format

    elif isinstance(materials_raw, list):
        normalized = {}
        for entry in materials_raw:
            name = entry.get("name")
            quantity = entry.get("quantity", 0)
            category = entry.get("category", "Other")
            if not name:
                continue

            if category not in normalized:
                normalized[category] = {}
            normalized[category][name] = quantity

        return normalized

    else:
        # fallback to empty
        return {}

def get_material_quantity(blueprint, material_name):
    quantity = 0

    materials = blueprint.materials

    if isinstance(materials, dict):
        for sub_category in materials.values():
            if isinstance(sub_category, dict):
                quantity += sub_category.get(material_name, 0)
            elif isinstance(sub_category, list):  # optional fallback
                for item in sub_category:
                    if isinstance(item, dict) and item.get("name") == material_name:
                        quantity += item.get("quantity", 0)
    elif isinstance(materials, list):
        for item in materials:
            if isinstance(item, dict) and item.get("name") == material_name:
                quantity += item.get("quantity", 0)

    return quantity


def fetch_price(type_id, station_id, headers):
    if station_id:
        price_data = get_station_sell_price(type_id, station_id, headers)  # returns tuple (price, source)
        price, source = price_data
        if price is not None:
            return type_id, price_data, False  # No fallback because station price found
        # fallback to Jita
        price_data = get_lowest_jita_sell_price(type_id, headers)
        return type_id, price_data, True  # fallback occurred
    else:
        price_data = get_lowest_jita_sell_price(type_id, headers)
        return type_id, price_data, False



def get_item_info(material_names):
    # Get the path to the SDE
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    sde_path = os.path.join(base_path, 'sde', 'mini_sde.sqlite')
    
    if not os.path.exists(sde_path):
        logger.error(f"SDE database not found at: {sde_path}")
        raise FileNotFoundError(f"SDE database not found at: {sde_path}")

    # Connect to the SDE database
    conn = sqlite3.connect(sde_path)
    cursor = conn.cursor()

    # Normalize the material names
    normalized_names = [unicodedata.normalize('NFC', normalize_name(name)) for name in material_names]

    # Query the SDE database
    placeholders = ', '.join('?' for _ in normalized_names)
    query = f'''
    SELECT i.typeName, i.typeID, COALESCE(m.manufacturingCategory, 'Other')
    FROM invTypes i
    LEFT JOIN materialClassifications m ON i.typeID = m.typeID
    WHERE i.typeName IN ({placeholders})
    '''
    cursor.execute(query, normalized_names)
    rows = cursor.fetchall()

    info = {}
    for name, tid, cat in rows:
        info[normalize_name(name)] = {"type_id": tid, "category": cat}
    
    if not info:
        logger.debug("No material info found")

    conn.close()

    # Return the material information
    return {
        normalize_name(name): info.get(normalize_name(name), {"type_id": 0, "category": "Other"})
        for name in material_names
    }

def compute_expanded_materials(blueprint, quantity, blueprints):
    """Returns dict of materials (including Items) required to produce quantity units of blueprint"""
    t1_deps = defaultdict(float)
    expanded = expand_materials(blueprint, blueprints, quantity=quantity, t1_dependencies=t1_deps)
    combined = defaultdict(float, expanded)
    for k, v in t1_deps.items():
        combined[k] += v
    return combined

def get_item_name(type_id):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    sde_path = os.path.join(base_path, 'sde', 'mini_sde.sqlite')

    if not os.path.exists(sde_path):
        logger.error(f"SDE database not found at: {sde_path}")
        raise FileNotFoundError(f"SDE database not found at: {sde_path}")

    conn = sqlite3.connect(sde_path)
    cursor = conn.cursor()

    cursor.execute('SELECT typeName FROM invTypes WHERE typeID = ?', (type_id,))
    result = cursor.fetchone()

    conn.close()

    return result[0] if result else None




def parse_blueprint_text(raw_text, category_lookup=None):
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    if not lines:
        return {}, "Unknown", 0
    # --- ISK/hour format detection ---
    if any("Component Material List" in l for l in lines):
        return parse_iskhour_format(lines, category_lookup)
    # --- In-game format detection ---
    if any("Blueprint" in l and "\t" in l for l in lines):
        return parse_ingame_format(lines, category_lookup)
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



from collections import defaultdict

def parse_ingame_format(lines, category_lookup=None):
    # First line contains blueprint name and typeID
    first_line_parts = lines[0].split('\t')
    blueprint_name = first_line_parts[0].replace(' Blueprint', '').strip()

    materials_by_category = defaultdict(dict)

    if category_lookup is None:
        category_lookup = {}

    for line in lines[1:]:
        clean_line = line.strip()
        if not clean_line or clean_line.lower().startswith(('item\t', 'material\t')):
            continue
        
        if '\t' in clean_line:
            parts = [p.strip() for p in clean_line.split('\t')]

            if len(parts) < 2:
                continue

            try:
                name = parts[0]
                quantity = int(float(parts[1]))

                category = category_lookup.get(name, 'Uncategorized')
                materials_by_category[category][name] = quantity
            except Exception:
                continue

    return materials_by_category, blueprint_name


def get_material_category_lookup():
    lookup = {}

    # Known minerals (fallbacks)
    known_minerals = {
        'Tritanium', 'Pyerite', 'Mexallon', 'Isogen',
        'Nocxium', 'Zydrine', 'Megacyte', 'Morphite'
    }
    for mineral in known_minerals:
        lookup[mineral] = "Minerals"

    # Scan through all blueprint materials
    blueprints = Blueprint.query.all()
    for bp in reversed(blueprints):  # prioritize newer blueprints
        if isinstance(bp.materials, dict):
            for cat_or_material, contents in bp.materials.items():
                if isinstance(contents, dict):  # Nested form {category: {material: qty}}
                    for mat in contents:
                        lookup[mat] = cat_or_material
                else:  # Flat form {material: qty}
                    lookup[cat_or_material] = "Uncategorized"

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

JITA_STATION_ID = 60003760

import time

cache = {}

def get_lowest_jita_sell_price(type_id, headers, retries=2):
    url = f"https://esi.evetech.net/latest/markets/{JITA_REGION_ID}/orders/?order_type=sell&type_id={type_id}"

    cached = cache.get(type_id)
    local_headers = headers.copy()

    use_cache = False

    if cached:
        age = time.time() - cached.get("timestamp", 0)
        if age < PRICE_CACHE_TTL:
            local_headers["If-None-Match"] = cached["etag"]
            use_cache = True
        else:
            logger.info(f"Cache expired for {type_id} (age={age:.1f}s)")

    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=local_headers, timeout=10)

            if response.status_code == 304 and cached and use_cache:
                logger.info(f"Used cached data for type_id {type_id}")
                return cached["lowest_price"], "cached"


            response.raise_for_status()

            etag = response.headers.get("ETag")
            orders = response.json()
            jita_orders = [o for o in orders if o.get("location_id") == JITA_STATION_ID]
            if not jita_orders:
                logger.warning(f"No Jita 4-4 orders for {type_id}, falling back to region")
                jita_orders = orders

            if not jita_orders:
                return None, "not_found"

            lowest_price = min(order["price"] for order in jita_orders)

            # Cache result
            if etag:
                cache[type_id] = {
                    "etag": etag,
                    "lowest_price": lowest_price,
                    "timestamp": time.time()
                }

            return lowest_price, "jita"
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {e}")
            time.sleep(1)

    return None, "error"

def get_lowest_jita_sell_prices_loop(type_ids: list[int], headers, retries=2) -> dict[int, float | None]:
    """
    Loop-based version of batch price fetch, since ESI doesn't support true batching.
    Uses your caching-aware get_lowest_jita_sell_price.
    """
    prices = {}

    for tid in type_ids:
        price, _ = get_lowest_jita_sell_price(tid, headers=headers, retries=retries)
        prices[tid] = price if price is not None else 0.0

    return prices


# Temporary cache for structure orders
structure_order_cache = defaultdict(list)

#TODO: add search by region


# Cache becomes: { station_id: (timestamp, [orders]) }
structure_order_cache = {}

CACHE_TTL = 60 * 5  # 5 minutes

def get_station_sell_price(type_id, station_id, headers):
    now = time.time()
    cached = structure_order_cache.get(station_id)
    use_cache = False

    if cached:
        age = now - cached[0]
        if age < CACHE_TTL:
            logger.debug(f"Using cached data for station {station_id} (age: {age:.1f}s)")
            use_cache = True
        else:
            logger.info(f"Cache expired for station {station_id} (age: {age:.1f}s)")

    if not use_cache:
        url = f"https://esi.evetech.net/latest/markets/structures/{station_id}/"
        all_orders = []
        page = 1

        try:
            logger.info(f"Fetching structure orders at {station_id}")

            while True:
                paged_url = f"{url}?page={page}"
                res = requests.get(paged_url, headers=headers)

                if res.status_code == 500:
                    logger.warning(f"Server error on page {page} — stopping early.")
                    break

                res.raise_for_status()
                page_orders = res.json()
                all_orders.extend(page_orders)

                logger.info(f"Fetched page {page} with {len(page_orders)} orders.")
                if len(page_orders) < 1000:
                    break
                page += 1

            # Update cache
            structure_order_cache[station_id] = (now, all_orders)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch structure orders from {station_id}: {e}")
            return None, "error"
    else:
        all_orders = cached[1]

    # Filter sell orders for this type_id
    sell_orders = [
        order for order in all_orders
        if not order['is_buy_order'] and order['type_id'] == type_id
    ]

    if not sell_orders:
        logger.warning(f"No sell orders for type_id {type_id} at structure {station_id}")
        return None, "not_found"

    lowest = min(order['price'] for order in sell_orders)
    logger.info(f"Lowest sell price for type_id {type_id} at structure {station_id}: {lowest}")

    return lowest, "structure"





def refresh_access_token():
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return None

    response = requests.post(
        TOKEN_URL,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code == 200:
        data = response.json()
        session["token"] = data.get("access_token")
        return session["token"]
    else:
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




def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "token" not in session or not session["token"]:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function
