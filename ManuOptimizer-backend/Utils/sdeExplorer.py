import sys
import os
import sqlite3

# Point to MINI SDE (the one you manually verified has invTypes)
SDE_PATH = r"C:\Users\nario\Documents\Coding Stuff\Eve-Code\ManuOptimizer\ManuOptimizer-backend\Utils\mini_sde.sqlite"

def check_tables():
    conn = sqlite3.connect(SDE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:")
    for table in tables:
        print(f"  - {table[0]}")
    conn.close()

def check_exact_name(type_name: str):
    conn = sqlite3.connect(SDE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT typeID, typeName FROM invTypes WHERE typeName = ?",
        (type_name,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        print(f"FOUND in SDE: typeID={row[0]}, typeName='{row[1]}'")
    else:
        print(f"NOT FOUND in SDE: '{type_name}'")

def test_name_match():
    conn = sqlite3.connect(SDE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT typeID, typeName FROM invTypes WHERE typeName LIKE '%Cynosural%'")
    rows = cursor.fetchall()
    for tid, name in rows:
        print(f">>> ({tid}) '{name}'")
    conn.close()

if __name__ == "__main__":
    check_tables()  # See what tables actually exist
    test_name_match()
    check_exact_name("Mining Laser Efficiency Charge")
    check_exact_name("Mining Laser Efficiency Charge Blueprint")
