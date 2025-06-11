import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_type_ids_from_esi


from models import BlueprintT2, db, Blueprint, Material

# rest of your utils.py code



if __name__ == "__main__":
    test_names = ["Armor Plates", "Tritanium", "Unknown Item"]

    for name in test_names:
        type_id = get_type_ids_from_esi(name)
        print(f"Material: {name}, type_id: {type_id}")