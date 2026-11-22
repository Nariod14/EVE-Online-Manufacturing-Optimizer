"""Buy allow-list: the materials the optimizer may put on the shopping list.

GET  /api/buylist             the list, with prices
PUT  /api/buylist             {"names": [...]} replaces the list and prices new entries
GET  /api/buylist/candidates  every input your blueprints use, to pick from
"""
import concurrent.futures
import logging
import traceback

from flask import Blueprint, jsonify, request

from models import Blueprint as BlueprintModel, BuyListItem, Material, db
from .optimizer_core import INVENTION_SECTION, split_materials
from .utils import fetch_price, get_item_info, normalize_name

logger = logging.getLogger(__name__)

buylist_bp = Blueprint('buylist', __name__, url_prefix='/api/buylist')

ESI_HEADERS = {'User-Agent': 'ManuOptimizer 1.0'}


def refresh_buy_list_prices(items, headers=None):
    """Fetch the Jita lowest sell price for each BuyListItem (in place, no commit).

    Items whose price cannot be fetched keep their previous price.
    Returns the names that have no price afterwards.
    """
    headers = headers or ESI_HEADERS
    jobs = {i.type_id for i in items if i.type_id}
    prices = {}
    if jobs:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_price, tid, None, headers) for tid in jobs]
            for future in concurrent.futures.as_completed(futures):
                try:
                    tid, (price, _source), _fallback = future.result()
                except Exception:
                    logger.warning("Buy list price fetch failed", exc_info=True)
                    continue
                if price is not None:
                    prices[tid] = price
    for item in items:
        if item.type_id in prices:
            item.sell_price = prices[item.type_id]
    return [i.name for i in items if not i.sell_price]


def _serialize(item):
    return {"name": item.name, "type_id": item.type_id, "sell_price": item.sell_price}


@buylist_bp.route('', methods=['GET'])
def get_buy_list():
    try:
        items = BuyListItem.query.order_by(BuyListItem.name).all()
        return jsonify([_serialize(i) for i in items]), 200
    except Exception:
        logger.error("Error getting buy list!\n" + traceback.format_exc())
        return jsonify({"error": "An error occurred while getting the buy list"}), 500


@buylist_bp.route('', methods=['PUT'])
def set_buy_list():
    """Replace the buy list. Body: {"names": ["Nocxium", "Tritanium", ...]}."""
    try:
        data = request.get_json(silent=True) or {}
        names = data.get("names")
        if not isinstance(names, list):
            return jsonify({"error": "Expected {\"names\": [...]}"}), 400
        wanted = []
        for n in names:
            if isinstance(n, str) and n.strip():
                n = normalize_name(n)
                if n not in wanted:
                    wanted.append(n)

        existing = {i.name: i for i in BuyListItem.query.all()}
        for name, item in existing.items():
            if name not in wanted:
                db.session.delete(item)

        new_names = [n for n in wanted if n not in existing]
        unknown = []
        new_items = []
        if new_names:
            info = get_item_info(new_names)
            for name in new_names:
                tid = info.get(name, {}).get("type_id") or None
                if not tid:
                    unknown.append(name)
                    continue
                item = BuyListItem(name=name, type_id=tid)
                db.session.add(item)
                new_items.append(item)

        # Price only the new entries here; "Update prices" refreshes the whole list.
        no_price = refresh_buy_list_prices(new_items) if new_items else []
        db.session.commit()

        items = BuyListItem.query.order_by(BuyListItem.name).all()
        return jsonify({
            "items": [_serialize(i) for i in items],
            "unknown": unknown,      # names not found in the SDE, not added
            "no_price": no_price,    # added, but no market price yet
        }), 200
    except Exception:
        db.session.rollback()
        logger.error("Error setting buy list!\n" + traceback.format_exc())
        return jsonify({"error": "An error occurred while saving the buy list"}), 500


@buylist_bp.route('/candidates', methods=['GET'])
def get_candidates():
    """Every raw input used by a blueprint (not invention materials, not things you build)."""
    try:
        blueprints = BlueprintModel.query.all()
        built = {b.name for b in blueprints}
        stock = {m.name: m for m in Material.query.all()}
        on_list = {i.name: i for i in BuyListItem.query.all()}

        found = {}
        for b in blueprints:
            inputs, _invention, categories = split_materials(b.materials)
            for name in inputs:
                if name in built or categories.get(name) == INVENTION_SECTION:
                    continue
                found.setdefault(name, categories.get(name) or "Other")
        for name in on_list:                    # keep listed items visible even if unused now
            found.setdefault(name, "Other")

        result = []
        for name, category in found.items():
            mat = stock.get(name)
            listed = on_list.get(name)
            price = (listed.sell_price if listed and listed.sell_price else None) \
                or (mat.sell_price if mat and mat.sell_price else None)
            result.append({
                "name": name,
                "category": (mat.category if mat and mat.category else category),
                "sell_price": price,
                "in_stock": int(mat.quantity) if mat else 0,
                "on_list": listed is not None,
            })
        result.sort(key=lambda r: (r["category"], r["name"]))
        return jsonify(result), 200
    except Exception:
        logger.error("Error getting buy list candidates!\n" + traceback.format_exc())
        return jsonify({"error": "An error occurred while getting the candidates"}), 500
