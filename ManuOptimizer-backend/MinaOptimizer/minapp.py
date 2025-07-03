# MinaOptimizer/mining_planner/logic.py

import collections

# Ore yields (post-Equinox, nullsec, simplified for main minerals)
ORE_YIELDS = {
    'Mordunium':      {'Tritanium': 100, 'Pyerite': 96},
    'Hezorime':       {'Mexallon': 120, 'Zydrine': 30},
    'Nocxite':        {'Nocxium': 80},
    'Ueganite':       {'Isogen': 60, 'Zydrine': 20, 'Megacyte': 40},
    'Griemeer':       {'Isogen': 100},
    'Kylixium':       {'Mexallon': 160},
    'Veldspar':       {'Tritanium': 100},
    'Mercoxit':       {'Morphite': 300},  # Not used in your modules, but included for completeness
}

# For the schedule, map minerals to best ores
MINERAL_TO_ORE = {
    'Tritanium': ['Mordunium', 'Veldspar'],
    'Pyerite': ['Mordunium'],
    'Mexallon': ['Hezorime', 'Kylixium'],
    'Isogen': ['Griemeer', 'Ueganite'],
    'Nocxium': ['Nocxite'],
    'Zydrine': ['Hezorime', 'Ueganite'],
    'Megacyte': ['Ueganite'],
}

MINING_SCHEDULE = [
    {"day": "Monday",    "ore": "Hezorime/Ueganite", "minerals": "Mexallon, Zydrine, Megacyte", "notes": "Bottleneck minerals"},
    {"day": "Tuesday",   "ore": "Nocxite",           "minerals": "Nocxium",                     "notes": "Rare, essential"},
    {"day": "Wednesday", "ore": "Mordunium",         "minerals": "Tritanium, Pyerite",          "notes": "Bulk minerals"},
    {"day": "Thursday",  "ore": "Griemeer",          "minerals": "Isogen",                      "notes": "Top up Isogen if needed"},
    {"day": "Friday",    "ore": "Hezorime/Ueganite", "minerals": "Mexallon, Zydrine, Megacyte", "notes": "Catch up on rare minerals"},
    {"day": "Saturday",  "ore": "Mordunium",         "minerals": "Tritanium, Pyerite",          "notes": "Bulk refill or flex"},
    {"day": "Sunday",    "ore": "Flex/Market/Rest",  "minerals": "Whatever is lowest",           "notes": "Fill gaps, haul, refine, rest"},
]

def flatten_blueprint_materials(blueprints):
    """
    Given a list of Blueprint SQLAlchemy objects,
    returns a dict of total mineral requirements (summed across all blueprints).
    Only counts the 7 main minerals.
    """
    minerals = ['Tritanium', 'Pyerite', 'Mexallon', 'Isogen', 'Nocxium', 'Zydrine', 'Megacyte']
    total = collections.Counter()
    for bp in blueprints:
        mats = bp.materials
        if isinstance(mats, dict):
            for section, section_mats in mats.items():
                if isinstance(section_mats, dict):
                    for mat, qty in section_mats.items():
                        if mat in minerals:
                            total[mat] += qty
    return dict(total)

def calculate_deficits(total_needed, inventory):
    """
    Returns a dict of {mineral: deficit} (how much you need to mine)
    """
    deficits = {}
    for mineral, needed in total_needed.items():
        have = inventory.get(mineral, 0)
        deficit = max(needed - have, 0)
        deficits[mineral] = deficit
    return deficits

def prioritize_minerals(deficits):
    """
    Returns a sorted list of minerals, most bottlenecked first.
    """
    # Sort by deficit descending
    return sorted(deficits.items(), key=lambda x: x[1], reverse=True)

def suggest_ores(deficits):
    """
    For each mineral with a deficit, suggest the best ore(s) to mine.
    """
    suggestions = []
    for mineral, amount in deficits.items():
        if amount > 0:
            ores = MINERAL_TO_ORE.get(mineral, [])
            suggestions.append({
                "mineral": mineral,
                "amount": amount,
                "ores": ores,
                "reason": f"Deficit of {amount:,} {mineral}, best mined from {', '.join(ores)}"
            })
    return suggestions

def build_mining_plan(blueprints, materials):
    total_needed = flatten_blueprint_materials(blueprints)
    total_all_minerals = sum(total_needed.values())
    
    # Calculate ratio of each mineral to total required
    mineral_ratios = {m: (qty / total_all_minerals) for m, qty in total_needed.items()}
    
    # Calculate deficit ratios (deficit / total_needed)
    deficits = calculate_deficits(total_needed, materials)
    deficit_ratios = {m: (deficit / total_needed[m]) if total_needed[m] > 0 else 0 
                      for m, deficit in deficits.items()}
    
    # Priority score = ratio * deficit_ratio (higher = more critical)
    priority_scores = {m: mineral_ratios[m] * deficit_ratios[m] 
                       for m in total_needed.keys()}
    
    # Sort minerals by priority score (descending)
    prioritized = sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Generate ore priorities (favor ores with multiple high-score minerals)
    ore_scores = collections.defaultdict(float)
    for mineral, score in prioritized:
        for ore in MINERAL_TO_ORE.get(mineral, []):
            ore_scores[ore] += score  # Ores get score from all their minerals
    
    # Sort ores by their total score
    ore_priority = sorted(ore_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Build schedule dynamically based on top ores
    schedule = []
    top_ores = [ore for ore, _ in ore_priority[:3]]  # Top 3 ores
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, day in enumerate(days):
        if i < len(top_ores):
            ore = top_ores[i]
            minerals = list(ORE_YIELDS[ore].keys()) if ore in ORE_YIELDS else []
            schedule.append({
                "day": day,
                "ore": ore,
                "minerals": ", ".join(minerals),
                "notes": f"Top priority ore: covers {', '.join(minerals)}"
            })
        else:
            schedule.append({
                "day": day,
                "ore": "Flex",
                "minerals": "Remaining minerals",
                "notes": "Fill gaps based on current deficits"
            })
    
    return {
        "status": "ok",
        "priority_scores": prioritized,
        "ore_priority": ore_priority,
        "schedule": schedule
    }
