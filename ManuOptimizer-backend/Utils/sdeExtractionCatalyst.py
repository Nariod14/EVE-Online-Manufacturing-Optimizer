import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SDE_PATH = os.path.join(BASE_DIR, 'sde.sqlite')
MINI_SDE_PATH = os.path.join(BASE_DIR, 'mini_sde.sqlite')

# ── Classification maps ────────────────────────────────────────────────────────

# Checked first — groupName takes priority over categoryName
MANUFACTURING_GROUP_MAP = {
    # Minerals
    'Mineral':                                  'Minerals',
    'Unrefined Mineral':                        'Minerals',

    # Reaction Materials
    'Ice Product':                              'Reaction Materials',
    'Moon Materials':                           'Reaction Materials',
    'Hybrid Polymers':                          'Reaction Materials',
    'Composite':                                'Reaction Materials',
    'Intermediate Materials':                   'Reaction Materials',
    'Biochemical Material':                     'Reaction Materials',
    'Abyssal Materials':                        'Reaction Materials',
    'Molecular-Forged Materials':               'Reaction Materials',
    'Sleeper Components':                       'Reaction Materials',
    'Hybrid Tech Components':                   'Reaction Materials',
    'Harvestable Cloud':                        'Reaction Materials',
    'Compressed Gas':                           'Reaction Materials',

    # Fuel
    'Fuel Block':                               'Fuel',

    # Salvage
    'Salvaged Materials':                       'Salvage',
    'Ancient Salvage':                          'Salvage',

    # Components
    'Named Components':                         'Components',
    'Construction Components':                  'Components',
    'Capital Construction Components':          'Components',
    'Unknown Components':                       'Components',
    'Advanced Capital Construction Components': 'Advanced Components',
    'Structure Components':                     'Structure Components',

    # Invention Materials (from Commodity category)
    'Datacores':                                'Invention Materials',
    'Decryptors - Sleepers':                    'Invention Materials',
}

# Checked second — categoryName fallback
MANUFACTURING_CATEGORY_MAP = {
    'Asteroid':             'Minerals',
    'Ship':                 'Items',
    'Module':               'Items',
    'Structure Module':     'Items',
    'Starbase':             'Items',
    'Charge':               'Items',
    'Drone':                'Items',
    'Subsystem':            'Items',
    'Fighter':              'Items',
    'Deployable':           'Items',
    'Structure':            'Items',
    'Reaction':             'Reaction Materials',
    'Ancient Relics':       'Invention Materials',
    'Decryptors':           'Invention Materials',
    'Blueprint':            'Invention Materials',
    'Planetary Commodities':'Planetary Materials',
}

# ── Build mini SDE ─────────────────────────────────────────────────────────────

if os.path.exists(MINI_SDE_PATH):
    os.remove(MINI_SDE_PATH)

full_conn = sqlite3.connect(SDE_PATH)
full_conn.row_factory = sqlite3.Row
full_cursor = full_conn.cursor()

mini_conn = sqlite3.connect(MINI_SDE_PATH)
mini_cursor = mini_conn.cursor()

# ── Create tables ──────────────────────────────────────────────────────────────

mini_cursor.execute('''
CREATE TABLE IF NOT EXISTS types (
    typeID   INTEGER PRIMARY KEY,
    typeName TEXT
)
''')

mini_cursor.execute('''
CREATE TABLE IF NOT EXISTS materialClassifications (
    typeID                INTEGER PRIMARY KEY,
    typeName              TEXT,
    groupID               INTEGER,
    groupName             TEXT,
    categoryID            INTEGER,
    categoryName          TEXT,
    manufacturingCategory TEXT
)
''')

# ── Fetch all items with full join ─────────────────────────────────────────────

full_cursor.execute('''
SELECT
    et.typeID,
    etn.en          AS typeName,
    et.groupID,
    gn.en           AS groupName,
    eg.categoryID,
    cn.en           AS categoryName,
    et.marketGroupID,
    mgn.en          AS marketGroupName,
    eg.published    AS groupPublished
FROM EveType et
JOIN EveTypeName etn   ON etn.parentTypeId  = et.typeID
JOIN EveGroup eg       ON eg.groupID        = et.groupID
JOIN GroupName gn      ON gn.parentTypeId   = et.groupID
JOIN CategoryName cn   ON cn.parentTypeId   = eg.categoryID
LEFT JOIN MarketGroupName mgn ON mgn.parentTypeId = et.marketGroupID
WHERE eg.published = 1
''')

rows = full_cursor.fetchall()

# ── Populate types table ───────────────────────────────────────────────────────

mini_cursor.executemany(
    "INSERT OR IGNORE INTO types (typeID, typeName) VALUES (?, ?)",
    [(row['typeID'], row['typeName']) for row in rows]
)

# ── Classify and populate materialClassifications ─────────────────────────────

classified = []

for row in rows:
    typeID       = row['typeID']
    typeName     = row['typeName']
    groupID      = row['groupID']
    groupName    = row['groupName']
    categoryID   = row['categoryID']
    categoryName = row['categoryName']

    # Group override takes priority
    manu_cat = MANUFACTURING_GROUP_MAP.get(groupName)

    # Fall back to category map
    if not manu_cat:
        manu_cat = MANUFACTURING_CATEGORY_MAP.get(categoryName)

    # Skip anything we don't care about
    if not manu_cat:
        continue

    classified.append((
        typeID, typeName,
        groupID, groupName,
        categoryID, categoryName,
        manu_cat
    ))

mini_cursor.executemany('''
INSERT OR IGNORE INTO materialClassifications
(typeID, typeName, groupID, groupName, categoryID, categoryName, manufacturingCategory)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', classified)

mini_conn.commit()

# ── Summary ────────────────────────────────────────────────────────────────────

mini_cursor.execute('''
SELECT manufacturingCategory, COUNT(*) as cnt
FROM materialClassifications
GROUP BY manufacturingCategory
ORDER BY cnt DESC
''')

print("\n── materialClassifications breakdown ──")
for r in mini_cursor.fetchall():
    print(f"  {r[0]:<25} {r[1]}")

mini_cursor.execute("SELECT COUNT(*) FROM types")
print(f"\n── types table: {mini_cursor.fetchone()[0]} total items ──")

mini_cursor.execute('''
    CREATE VIEW IF NOT EXISTS invTypes AS SELECT * FROM types
''')
mini_conn.commit()

full_conn.close()
mini_conn.close()

print("\nDone! mini_sde.sqlite written.")