import requests
import logging

# Constants
JITA_REGION_ID = 10000002  # The Forge
JITA_STATION_ID = 60003760  # Caldari Navy Assembly Plant

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "ManuOptimizer 1.0 nariod14@gmail.com"
}

def get_lowest_jita_sell_price(type_id):
    url = f"https://esi.evetech.net/latest/markets/{JITA_REGION_ID}/orders/?order_type=sell&type_id={type_id}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        orders = response.json()

        # Filter only orders from Jita 4-4
        jita_orders = [o for o in orders if o.get("location_id") == JITA_STATION_ID]
        if not jita_orders:
            logger.warning(f"No Jita orders for type_id {type_id}, falling back to region-wide.")
            jita_orders = orders  # Use full list

        if not jita_orders:
            logger.warning(f"No sell orders at all for type_id {type_id}")
            return None


        lowest_price = min(order['price'] for order in jita_orders)
        logger.info(f"Lowest sell price for type_id {type_id} at Jita 4-4: {lowest_price}")
        return lowest_price

    except Exception as e:
        logger.error(f"Error fetching Jita sell price for type_id {type_id}: {e}")
        return None


# === Quick test ===
if __name__ == "__main__":
    test_ids = {
        "Tritanium": 34,
        "Small Tractor Beam I": 2893,
        "Medium Asteroid Ore Compressor I": 62688,
        "Bastion Module I": 30532,
    }

    for name, tid in test_ids.items():
        logger.info(f"Checking price for {name} (type_id: {tid})")
        get_lowest_jita_sell_price(tid)
