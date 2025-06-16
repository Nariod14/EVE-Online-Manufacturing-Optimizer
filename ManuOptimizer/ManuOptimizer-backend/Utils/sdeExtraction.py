import sqlite3

# Path to full SDE
SDE_PATH = r"C:\Users\nario\Documents\Coding Stuff\Eve-Code\ManuOptimizer\Utils\sde.sqlite"

# Output mini SDE
mini_conn = sqlite3.connect('mini_sde.sqlite')
mini_cursor = mini_conn.cursor()

# Load full SDE
full_conn = sqlite3.connect(SDE_PATH)
full_cursor = full_conn.cursor()

####################################
# 1. Create invTypes table
####################################
mini_cursor.execute('''
CREATE TABLE IF NOT EXISTS invTypes (
    typeID INTEGER PRIMARY KEY,
    typeName TEXT
)
''')

full_cursor.execute('SELECT typeID, typeName FROM invTypes WHERE published = 1')
invtype_rows = full_cursor.fetchall()
mini_cursor.executemany("INSERT INTO invTypes (typeID, typeName) VALUES (?, ?)", invtype_rows)

####################################
# 2. Create materialClassifications table
####################################
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
    # True Minerals
    'Minerals': 'Minerals',

    # Planetary Interaction
    'Planetary Commodities': 'Planetary Materials',
    'Refined Commodities': 'Planetary Materials',

    # Reactions
    'Intermediate Materials': 'Reaction Materials',
    'Processed Materials': 'Reaction Materials',
    'Hybrid Polymers': 'Reaction Materials',
    'Advanced Moon Materials': 'Reaction Materials',
    'Composite Materials': 'Reaction Materials',
    'Gas Clouds': 'Reaction Materials',
    'Ice Products': 'Reaction Materials',

    # Components
    'Components': 'Components',
    'Advanced Components': 'Advanced Components',
    'Structure Components': 'Structure Components',
    'Construction Components': 'Components',

    # Salvage
    'Salvaged Materials': 'Salvage',

    # Other pre-defined T1 modules
    'Fuel Blocks': 'Fuel',
    'Datacores': 'Invention Materials',
    'Decryptors': 'Invention Materials',
}

# Build groupID -> manufacturing category
full_cursor.execute('SELECT groupID, groupName FROM invGroups')
group_map = full_cursor.fetchall()
group_to_category = {
    group_id: MANUFACTURING_GROUP_MAP.get(group_name)
    for group_id, group_name in group_map
    if MANUFACTURING_GROUP_MAP.get(group_name)
}

####################################
# 3. Fetch all relevant items
####################################
full_cursor.execute('''
SELECT t.typeID, t.typeName, g.groupID, g.groupName, c.categoryID, c.categoryName
FROM invTypes t
JOIN invGroups g ON t.groupID = g.groupID
JOIN invCategories c ON g.categoryID = c.categoryID
WHERE t.published = 1
''')

rows = full_cursor.fetchall()
inserted_ids = set()

filtered = []
for typeID, typeName, groupID, groupName, categoryID, categoryName in rows:
    manu_cat = group_to_category.get(groupID)

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

####################################
# 4. Insert filtered materials
####################################
mini_cursor.executemany('''
INSERT OR IGNORE INTO materialClassifications 
(typeID, typeName, groupID, groupName, categoryID, categoryName, manufacturingCategory)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', filtered)

####################################
# 5. Hardcode core minerals if not already present
####################################
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

####################################
# 6. Finalize
####################################
mini_conn.commit()
full_conn.close()
mini_conn.close()
