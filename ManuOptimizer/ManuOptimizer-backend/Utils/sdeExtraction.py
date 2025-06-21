import sqlite3

# Path to full SDE
SDE_PATH = r"C:\Users\nario\Documents\Coding Stuff\Eve-Code\ManuOptimizer\Utils\sde.sqlite"

# Output mini SDE
mini_conn = sqlite3.connect('mini_sde.sqlite')
mini_cursor = mini_conn.cursor()

# Load full SDE
full_conn = sqlite3.connect(SDE_PATH)
full_cursor = full_conn.cursor()

# 1. Create invTypes table

mini_cursor.execute('''
CREATE TABLE IF NOT EXISTS invTypes (
    typeID INTEGER PRIMARY KEY,
    typeName TEXT
)
''')

full_cursor.execute('SELECT typeID, typeName FROM invTypes WHERE published = 1')
invtype_rows = full_cursor.fetchall()
mini_cursor.executemany("INSERT INTO invTypes (typeID, typeName) VALUES (?, ?)", invtype_rows)

# 2. Create materialClassifications table
mini_cursor.execute('''
CREATE TABLE IF NOT EXISTS materialClassifications (
    typeID INTEGER PRIMARY KEY,
    typeName TEXT,
    groupID INTEGER,
    groupName TEXT,
    categoryID INTEGER,
    categoryName TEXT,
    manufacturingCategory TEXT
)
''')

# Mapping of groupName -> Manufacturing Category
MANUFACTURING_GROUP_MAP = {
    # Minerals and Raw
    'Minerals': 'Minerals',
    'Raw Moon Materials': 'Reaction Materials',
    'Ice Products': 'Reaction Materials',
    'Gas Clouds': 'Reaction Materials',

    # Processed and Advanced Reactions
    'Processed Moon Materials': 'Reaction Materials',
    'Advanced Moon Materials': 'Reaction Materials',
    'Hybrid Polymers': 'Reaction Materials',
    'Composite Materials': 'Reaction Materials',
    'Intermediate Materials': 'Reaction Materials',

    # Planetary Interaction
    'Planetary Materials': 'Planetary Materials',
    'Raw Planetary Materials': 'Planetary Materials',
    'Processed Planetary Materials': 'Planetary Materials',
    'Refined Planetary Materials': 'Planetary Materials',
    'Specialized Planetary Materials': 'Planetary Materials',
    'Advanced Planetary Materials': 'Planetary Materials',

    # Components
    'Components': 'Components',
    'Advanced Components': 'Advanced Components',
    'Structure Components': 'Structure Components',
    'Construction Components': 'Components',  # Legacy naming

    # Salvage
    'Salvaged Materials': 'Salvage',
    'Ancient Salvaged Materials': 'Salvage',

    # Items used in T2 production
    'Turrets & Bays': 'Items',
    'Hull & Armor': 'Items',
    'Propulsion': 'Items',
    'Engineering Equipment': 'Items',
    'Electronic Systems': 'Items',
    'Drones': 'Items',
    'Smartbombs': 'Items',
    'Energy Weapon': 'Items',
    'Missile Launchers': 'Items',
    'Energy Neutralizers': 'Items',
    'Energy Vampires': 'Items',
    'Electronic Warfare': 'Items',
    'Scanning Equipment': 'Items',
    'Warp Field Stabilizers': 'Items',
    'Shield Modifications': 'Items',
    'Weapon Upgrades': 'Items',
    'Drone Upgrades': 'Items',
    'Ship Modifications': 'Items',

    # Ammunition (used in some manufacturing chains)
    'Ammunition & Charges': 'Items',
    'Standard Ammo': 'Items',
    'Standard Charges': 'Items',
    'Standard Rockets': 'Items',
    'Standard Torpedoes': 'Items',
    'Missiles': 'Items',
    'Standard Light Missiles': 'Items',
    'Standard Heavy Missiles': 'Items',
    'Standard Cruise Missiles': 'Items',
    'Standard XL Torpedoes': 'Items',
    'Standard XL Cruise Missiles': 'Items',

    # Fuel
    'Fuel Blocks': 'Fuel',

    # Invention
    'Datacores': 'Invention Materials',
    'Decryptors': 'Invention Materials',

    # Rigs and Subsystems (used in manufacturing T2 ships)
    'Armor Rigs': 'Items',
    'Drone Rigs': 'Items',
    'Engineering Rigs': 'Items',
    'Energy Weapon Rigs': 'Items',
    'Hybrid Weapon Rigs': 'Items',
    'Missile Launcher Rigs': 'Items',
    'Projectile Weapon Rigs': 'Items',
    'Shield Rigs': 'Items',
    'Electronics Superiority Rigs': 'Items',
    'Subsystems': 'Items',
    'Subsystem Components': 'Items',

    # Misc
    'Tractor Beams': 'Items',
    'Mining Upgrades': 'Items',
    'Salvagers': 'Items',
    'Mining Lasers': 'Items',
    'Mining Crystals': 'Items',

    # Reaction Formulas (can be used for tech chaining)
    'Reaction Formulas': 'Invention Materials',
    'Simple Reactions': 'Invention Materials',
    'Complex Reactions': 'Invention Materials',
    'Polymer Reactions': 'Invention Materials',
    'Composite Reaction Formulas': 'Invention Materials',

    # Ancient Relics (used for T3 invention)
    'Ancient Relics': 'Invention Materials',

    # RAM and RDB
    'R.A.M.': 'Invention Materials',
    'R.Db': 'Invention Materials',
}


# Build marketGroupID -> manufacturing category
full_cursor.execute('SELECT marketGroupID, marketGroupName FROM invMarketGroups')
market_group_map = full_cursor.fetchall()

market_to_category = {
    mgid: MANUFACTURING_GROUP_MAP.get(mgname)
    for mgid, mgname in market_group_map
    if MANUFACTURING_GROUP_MAP.get(mgname)
}

# 3. Fetch all relevant items

full_cursor.execute('''
SELECT t.typeID, t.typeName, g.groupID, g.groupName, c.categoryID, c.categoryName, t.marketGroupID
FROM invTypes t
JOIN invGroups g ON t.groupID = g.groupID
JOIN invCategories c ON g.categoryID = c.categoryID
WHERE t.published = 1
''')

rows = full_cursor.fetchall()
inserted_ids = set()

filtered = []
for typeID, typeName, groupID, groupName, categoryID, categoryName, marketGroupID in rows:
    manu_cat = market_to_category.get(marketGroupID)


    # Check for explicit category match
    if manu_cat:
        filtered.append((typeID, typeName, groupID, groupName, categoryID, categoryName, manu_cat))
        inserted_ids.add(typeID)
        continue

    # Heuristic: If name ends in " I" and not " II", it's a T1 item
    if typeName.endswith(" I") and not typeName.endswith(" II"):
        if typeID not in inserted_ids:
            filtered.append((typeID, typeName, groupID, groupName, categoryID, categoryName, "Items"))
            inserted_ids.add(typeID)


# 4. Insert filtered materials
mini_cursor.executemany('''
INSERT OR IGNORE INTO materialClassifications 
(typeID, typeName, groupID, groupName, categoryID, categoryName, manufacturingCategory)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', filtered)

# 5. Hardcode core minerals if not already present
known_minerals = [
    "Tritanium", "Pyerite", "Mexallon", "Isogen",
    "Nocxium", "Zydrine", "Megacyte", "Morphite"
]

for mineral in known_minerals:
    full_cursor.execute('''
        SELECT t.typeID, t.typeName, g.groupID, g.groupName, c.categoryID, c.categoryName
        FROM invTypes t
        JOIN invGroups g ON t.groupID = g.groupID
        JOIN invCategories c ON g.categoryID = c.categoryID
        WHERE t.typeName = ? AND t.published = 1
    ''', (mineral,))
    row = full_cursor.fetchone()
    if row:
        typeID, typeName, groupID, groupName, categoryID, categoryName = row
        if typeID not in inserted_ids:
            try:
                mini_cursor.execute('''
                    INSERT INTO materialClassifications 
                    (typeID, typeName, groupID, groupName, categoryID, categoryName, manufacturingCategory)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (typeID, typeName, groupID, groupName, categoryID, categoryName, "Minerals"))
                inserted_ids.add(typeID)
            except sqlite3.IntegrityError:
                pass


# 6. Finalize
mini_conn.commit()
full_conn.close()
mini_conn.close()
