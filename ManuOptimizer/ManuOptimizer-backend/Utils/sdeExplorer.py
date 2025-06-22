import sqlite3

from utils import get_material_info

SDE_PATH = r"C:\Users\nario\Documents\Coding Stuff\Eve-Code\ManuOptimizer\Utils\sde.sqlite"

def test_name_match():
    conn = sqlite3.connect(SDE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT typeName FROM invTypes WHERE typeName LIKE '%Cynosural%'")
    rows = cursor.fetchall()
    for r in rows:
        print(f">>> '{r[0]}'")
    conn.close()


if __name__ == "__main__":
    test_name_match()
    print(get_material_info(["Covert Cynosural Field Generator I"])
)
