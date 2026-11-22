"""Production optimizer core for the EVE Manufacturing Optimizer.

Pure Python + PuLP: no Flask or database imports, so it can be tested on its own.
`routes/blueprints.py` calls `build_plan()` from the /optimize route.

Conventions (these match what is stored in the database):
  * blueprint.materials      quantities PER RUN, in either stored shape:
                               {"Category": {"Name": qty}}  or  [{"name", "quantity", "category"}]
  * blueprint.amt_per_run    units produced by one run (reactions, charges: more than 1)
  * blueprint.sell_price     price of ONE unit
  * blueprint.material_cost  cost of ONE run (T2: full_material_cost adds invention)
  * blueprint.max            cap on UNITS SOLD of that item per optimisation
                             (units built only to feed another blueprint do not count)

What the model decides:
  * run[b]   how many runs of each blueprint to install (integer)
  * sell[b]  how many of the units built are sold (integer, <= max)
  * draw[g]  how much of each stocked item is consumed (<= stock)
  * buy[g]   how much of each material to purchase (only when a budget is given)

Objective: sales revenue (after fees) - market value of the stock consumed
           - purchases - invention cost.
Stock is valued at its market price, so nothing is built unless it beats simply
selling the materials. That is the same yardstick the old route used
(sell_price - material_cost at Jita prices).
"""
from collections import defaultdict
import logging
import math

from pulp import (
    LpProblem, LpVariable, LpMaximize, LpStatus, lpSum, value, PULP_CBC_CMD,
)

logger = logging.getLogger(__name__)

INVENTION_SECTION = "Invention Materials"
ITEM_CATEGORY = "Items"
BUY_MODES = ("none", "list", "all")
LEGACY_BUY_MODES = {"minerals": "list"}   # old saved setting, now means "my buy list"


# --------------------------------------------------------------------------- helpers
def split_materials(raw):
    """Return (inputs, invention, categories) from either stored materials shape.

    inputs      {name: qty per run}   everything except invention materials
    invention   {name: qty per invention attempt}
    categories  {name: category}
    """
    inputs, invention, categories = defaultdict(float), defaultdict(float), {}
    if not raw:
        return {}, {}, {}

    def add(category, name, qty):
        if not name or qty is None:
            return
        try:
            qty = float(qty)
        except (TypeError, ValueError):
            return
        if category == INVENTION_SECTION:
            invention[name] += qty
        else:
            inputs[name] += qty
        categories[name] = category or "Other"

    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, dict):
                add(entry.get("category"), entry.get("name"), entry.get("quantity"))
    elif isinstance(raw, dict):
        for key, val in raw.items():
            if isinstance(val, dict):          # {"Category": {"Name": qty}}
                for name, qty in val.items():
                    add(key, name, qty)
            else:                              # flat {"Name": qty}
                add("Other", key, val)
    return dict(inputs), dict(invention), categories


def _num(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _chance(bp):
    """Invention chance as a fraction (accepts 45.3 or 0.453)."""
    c = _num(getattr(bp, "invention_chance", None))
    return c / 100.0 if c > 1 else c


def _invention_cost_per_run(bp):
    """ISK of invention attributable to one manufacturing run of a T2 blueprint."""
    if getattr(bp, "tier", "T1") != "T2":
        return 0.0
    full = getattr(bp, "full_material_cost", None)
    base = getattr(bp, "material_cost", None)
    if full is not None and base is not None and full > base:
        return float(full - base)
    chance = _chance(bp)
    runs_per_copy = _num(getattr(bp, "runs_per_copy", None), 1) or 1
    cost = _num(getattr(bp, "invention_cost", None))
    if chance > 0 and cost > 0:
        return cost / (chance * runs_per_copy)
    return 0.0


def _ceil(x):
    return int(math.ceil(x - 1e-6))


# --------------------------------------------------------------------------- model
def _solve(bps, goods, price, stock, buyable, budget, fee, integer, time_limit,
           volume=None, cargo_m3=None, cargo_buy=True, cargo_sell=True):
    cat = "Integer" if integer else "Continuous"
    names = list(bps)
    prob = LpProblem("MaxProfit", LpMaximize)

    run = {n: LpVariable(f"run_{i}", lowBound=0, cat=cat) for i, n in enumerate(names)}
    sell = {
        n: LpVariable(f"sell_{i}", lowBound=0, upBound=bps[n]["max"], cat=cat)
        for i, n in enumerate(names)
    }
    draw = {g: LpVariable(f"draw_{i}", lowBound=0, upBound=stock.get(g, 0)) for i, g in enumerate(goods)}
    buy = {
        g: LpVariable(f"buy_{i}", lowBound=0, upBound=None if g in buyable else 0)
        for i, g in enumerate(goods)
    }

    balance = {}
    for i, g in enumerate(goods):
        used = lpSum(b["inputs"][g] * run[n] for n, b in bps.items() if g in b["inputs"])
        made = bps[g]["apr"] * run[g] if g in bps else 0
        sold = sell[g] if g in bps else 0
        # consumed + sold  <=  built + taken from stock + bought
        balance[g] = (used + sold - made - draw[g] - buy[g] <= 0)
        prob += balance[g], f"bal_{i}"

    for i, n in enumerate(names):
        # only units built in this plan are sold; stock of a finished item feeds other builds
        prob += sell[n] <= bps[n]["apr"] * run[n], f"sellcap_{i}"

    purchases = lpSum(price.get(g, 0) * buy[g] for g in goods if g in buyable)
    if buyable:
        prob += purchases <= budget, "budget"
        if cargo_m3 and cargo_buy:
            # everything bought has to fit in the hauler (capacity x trips)
            prob += lpSum((volume or {}).get(g, 0) * buy[g] for g in buyable) <= cargo_m3, "cargo"

    if cargo_m3 and cargo_sell:
        # ...and so does everything hauled out to sell (a separate run of the same trips)
        volume = volume or {}
        prob += lpSum(volume[n] * sell[n] for n in names if n in volume) <= cargo_m3, "cargo_out"
        for i, n in enumerate(names):
            if n not in volume:            # cannot check it fits, so it is not sold
                prob += sell[n] <= 0, f"novol_{i}"

    revenue = lpSum(bps[n]["price"] * sell[n] for n in names)
    stock_value = lpSum(price.get(g, 0) * draw[g] for g in goods)
    invention = lpSum(bps[n]["invention_per_run"] * run[n] for n in names)
    # the tiny surcharge on purchases makes the solver use stock before buying the same item
    prob += revenue * (1 - fee) - stock_value - purchases * 1.0001 - invention

    prob.solve(PULP_CBC_CMD(msg=False, timeLimit=time_limit))
    return prob, run, sell, draw, buy, balance


def build_plan(blueprints, materials, budget=0.0, fee=0.0, buy_mode="none",
               buy_list=None, volumes=None, cargo_m3=None, cargo_buy=True, cargo_sell=True,
               time_limit=60, debug_lp_path=None):
    """Compute the most profitable production plan.

    blueprints  iterable of Blueprint rows (name, materials, sell_price, material_cost,
                amt_per_run, max, tier and, for T2, full_material_cost, invention_chance,
                invention_cost, runs_per_copy)
    materials   iterable of Material rows (name, quantity, sell_price, category)
    budget      ISK available for purchases. 0 means "inventory only" (the old behaviour).
    fee         sales tax + broker fee, as a fraction of revenue (0.05) or a percentage (5)
    buy_mode    "none" | "list" | "all"  which materials may be purchased
                ("minerals", the old setting, is read as "list")
    buy_list    {name: unit price or None}  the materials "list" mode may buy. Their
                prices also fill in for items with no Material row (nothing in stock).
    volumes     {name: m3 per unit}  needed when cargo_m3 is set
    cargo_m3    total m3 that everything bought must fit in (hauler capacity x trips),
                and, separately, everything sold. None or 0 = no limit. An item with
                no known volume is then neither bought nor sold.
    cargo_buy   apply cargo_m3 to purchases (default True)
    cargo_sell  apply cargo_m3 to sales (default True)

    Returns (result_dict, http_status).
    """
    budget = max(0.0, _num(budget))
    fee = _num(fee)
    if fee >= 1:
        fee /= 100.0
    fee = min(max(fee, 0.0), 0.99)
    buy_mode = LEGACY_BUY_MODES.get(buy_mode, buy_mode)
    if buy_mode not in BUY_MODES or budget <= 0:
        buy_mode = "none"
    buy_list = dict(buy_list or {})
    volumes = {n: _num(v) for n, v in (volumes or {}).items() if v is not None and _num(v) > 0}
    cargo_m3 = _num(cargo_m3)
    cargo_m3 = cargo_m3 if cargo_m3 > 0 else None
    cargo_buy, cargo_sell = bool(cargo_buy), bool(cargo_sell)

    warnings = []
    mat_by_name = {m.name: m for m in materials}
    stock = {n: max(0.0, _num(m.quantity)) for n, m in mat_by_name.items()}
    price = {n: _num(m.sell_price) for n, m in mat_by_name.items() if _num(m.sell_price) > 0}
    for n, p in buy_list.items():
        if _num(p) > 0:
            price.setdefault(n, _num(p))
    category = {n: (getattr(m, "category", None) or "Other") for n, m in mat_by_name.items()}

    bps = {}
    for b in blueprints:
        inputs, invention, cats = split_materials(b.materials)
        for n, c in cats.items():
            category.setdefault(n, c)
        unit_price = _num(b.sell_price)
        if unit_price <= 0:
            warnings.append(f"{b.name}: no sell price, so it is never built for sale")
        bps[b.name] = {
            "apr": max(1, int(round(_num(getattr(b, "amt_per_run", 1), 1))) or 1),
            "price": max(0.0, unit_price),
            "max": b.max if getattr(b, "max", None) is not None else None,
            "tier": getattr(b, "tier", "T1"),
            "inputs": {n: q for n, q in inputs.items() if q > 0 and n != b.name},
            "invention": invention,
            "invention_per_run": _invention_cost_per_run(b),
            "chance": _chance(b),
            "runs_per_copy": _num(getattr(b, "runs_per_copy", None), 1) or 1,
        }
        if unit_price > 0:
            price.setdefault(b.name, unit_price)   # a finished item is worth its sell price

    for n in bps:                                  # anything with a blueprint counts as an Item
        category[n] = ITEM_CATEGORY

    if not bps or not mat_by_name:
        return {"status": "No optimal solution found"}, 400

    goods = sorted(set(stock) | set(bps) | {g for b in bps.values() for g in b["inputs"]})

    for g in goods:
        if g not in price and any(g in b["inputs"] for b in bps.values()):
            if stock.get(g, 0) > 0:
                warnings.append(f"{g}: no price on record, so stock of it is treated as free")
            elif g not in bps:
                warnings.append(f"{g}: not in inventory and no price on record, so nothing that needs it can be built")

    if buy_mode == "list":
        if not buy_list:
            warnings.append("Your buy list is empty, so nothing is bought. Add materials to it first.")
        buyable = {g for g in goods if g in buy_list and g in price}
        for g in sorted(buy_list):
            if g not in price and any(g in b["inputs"] for b in bps.values()):
                warnings.append(f"{g}: on your buy list but has no price, so it cannot be bought. Update prices.")
    elif buy_mode == "all":
        buyable = {g for g in goods if g in price}
    else:
        buyable = set()

    if cargo_m3 and cargo_sell:
        for n in sorted(bps):
            if n not in volumes and bps[n]["price"] > 0:
                warnings.append(f"{n}: volume unknown, so it is not sold while a cargo limit is set")
    if cargo_m3 and cargo_buy and buyable:
        no_volume = sorted(g for g in buyable if g not in volumes)
        for g in no_volume:
            if any(g in b["inputs"] for b in bps.values()):
                warnings.append(f"{g}: volume unknown, so it is not bought while a cargo limit is set")
        buyable -= set(no_volume)

    prob, run, sell, draw, buy, _ = _solve(
        bps, goods, price, stock, buyable, budget, fee, integer=True, time_limit=time_limit,
        volume=volumes, cargo_m3=cargo_m3, cargo_buy=cargo_buy, cargo_sell=cargo_sell)

    status = LpStatus[prob.status]
    solved = prob.status == 1 or getattr(prob, "sol_status", 0) in (1, 2)
    if not solved:
        logger.info("Optimization status: %s", status)
        if debug_lp_path:
            try:
                with open(debug_lp_path, "w") as f:
                    f.write(str(prob))
            except OSError:
                pass
        return {"status": f"No optimal solution found: {status}"}, 400

    def val(v):
        x = value(v)
        return 0.0 if x is None else float(x)

    runs = {n: int(round(val(v))) for n, v in run.items()}
    sold = {n: int(round(val(v))) for n, v in sell.items()}
    drawn = {g: max(0.0, val(v)) for g, v in draw.items()}
    bought = {g: max(0.0, val(v)) for g, v in buy.items()}
    produced = {n: runs[n] * bps[n]["apr"] for n in bps}

    consumed = defaultdict(float)          # units of each good used as an input
    for n, b in bps.items():
        if runs[n]:
            for g, q in b["inputs"].items():
                consumed[g] += q * runs[n]

    # ---- money
    revenue = sum(bps[n]["price"] * sold[n] for n in bps)
    fees = revenue * fee
    stock_value_used = sum(price.get(g, 0) * drawn[g] for g in goods)
    purchase_cost = sum(price.get(g, 0) * bought[g] for g in goods)
    invention_cost = sum(bps[n]["invention_per_run"] * runs[n] for n in bps)
    true_profit = revenue - fees - stock_value_used - purchase_cost - invention_cost
    cash_profit = revenue - fees - purchase_cost - invention_cost

    # ---- stocked finished items used as inputs (e.g. T1 modules already on hand)
    inventory_items_used = {}
    inventory_cost_savings = 0.0
    for g in bps:
        if drawn.get(g, 0) > 1e-6:
            amount = int(round(drawn[g]))
            needed = _ceil(consumed.get(g, 0))
            inventory_items_used[g] = {
                "amount": amount,
                "category": ITEM_CATEGORY,
                "original_required": needed,
                "remaining_requirement": max(0, needed - amount),
            }
            inventory_cost_savings += amount * price.get(g, 0)

    # ---- intermediates that must be built for other blueprints (build these first)
    dependencies_needed = {}
    for n in bps:
        built_for_internal_use = produced[n] - sold[n]
        if built_for_internal_use > 0 and consumed.get(n, 0) > 1e-6:
            dependencies_needed[n] = int(built_for_internal_use)

    # ---- material usage
    #   raw materials:  used = taken from stock + bought, so a negative "remaining"
    #                   is exactly the amount on the shopping list
    #   items that have a blueprint: used = units consumed by other builds, so a
    #                   negative "remaining" is what has to be built (or bought)
    material_usage = {}
    for g in goods:
        if g in bps:
            used = consumed.get(g, 0)
            if g not in stock and used <= 1e-6:
                continue
        else:
            used = drawn.get(g, 0) + bought.get(g, 0)
            if g not in stock and used <= 1e-6:
                continue
        used_int = int(round(used))
        material_usage[g] = {
            "used": used_int,
            "remaining": int(round(stock.get(g, 0))) - used_int,
            "category": category.get(g, "Other"),
            "bought": _ceil(bought.get(g, 0)),
        }

    shopping_list = {
        g: {
            "quantity": _ceil(q),
            "unit_price": price.get(g, 0),
            "cost": round(q * price.get(g, 0), 2),
            "category": category.get(g, "Other"),
            "volume_m3": round(_ceil(q) * volumes[g], 2) if g in volumes else None,
        }
        for g, q in bought.items() if q > 1e-6
    }
    purchase_volume = round(sum(e["volume_m3"] or 0 for e in shopping_list.values()), 2)

    # ---- what goes to market: units sold, their m3 and sell value (before fees)
    sales = [
        {
            "name": n,
            "units": sold[n],
            "unit_volume": volumes.get(n),
            "volume_m3": round(sold[n] * volumes[n], 2) if n in volumes else None,
            "value": round(bps[n]["price"] * sold[n], 2),
        }
        for n in sorted(bps) if sold[n] > 0
    ]
    sell_volume = round(sum(s["volume_m3"] or 0 for s in sales), 2)

    # ---- datacores and other invention inputs (expected, given invention chance)
    invention_materials = defaultdict(float)
    for n, b in bps.items():
        if runs[n] and b["invention"]:
            attempts = runs[n] / b["runs_per_copy"]
            if b["chance"] > 0:
                attempts /= b["chance"]
            for g, q in b["invention"].items():
                invention_materials[g] += q * attempts
    expected_invention = {g: _ceil(q) for g, q in invention_materials.items() if q > 1e-6}

    # ---- marginal values: what one more unit of each material is worth to the plan
    marginal_values = []
    try:
        lp, _, _, _, _, lp_balance = _solve(
            bps, goods, price, stock, buyable, budget, fee, integer=False, time_limit=time_limit,
            volume=volumes, cargo_m3=cargo_m3, cargo_buy=cargo_buy, cargo_sell=cargo_sell)
        if lp.status == 1:
            for g in goods:
                if g in bps or stock.get(g, 0) <= 0:
                    continue
                dual = lp_balance[g].pi
                market = price.get(g, 0)
                if dual is None or market <= 0:
                    continue
                dual = abs(float(dual))
                if dual > market * 1.01:
                    marginal_values.append({
                        "name": g,
                        "category": category.get(g, "Other"),
                        "value": round(dual, 2),
                        "market_price": market,
                        "ratio": round(dual / market, 3),
                    })
            marginal_values.sort(key=lambda r: -r["ratio"])
    except Exception:                       # never let the extra report break the plan
        logger.warning("Could not compute marginal values", exc_info=True)

    what_to_produce = {n: r for n, r in runs.items() if r > 0}
    units_sold = {n: s for n, s in sold.items() if s > 0}
    units_produced = {n: p for n, p in produced.items() if p > 0}
    production_plan = [
        {
            "name": n,
            "tier": bps[n]["tier"],
            "runs": runs[n],
            "units_per_run": bps[n]["apr"],
            "units_produced": produced[n],
            "units_sold": sold[n],
            "units_for_other_builds": produced[n] - sold[n],
            "revenue": bps[n]["price"] * sold[n],
        }
        for n in sorted(bps) if runs[n] > 0
    ]

    result = {
        "status": "Optimal",

        # --- fields the frontend already used
        "total_profit": revenue,                      # historical name: this is the total sell value
        "true_profit_jita": true_profit,
        "true_profit_inventory": true_profit + inventory_cost_savings,
        "inventory_cost_savings": inventory_cost_savings,
        "what_to_produce": what_to_produce,           # runs to install, per blueprint
        "original_production_plan": what_to_produce,
        "adjusted_production_plan": units_sold,       # units to put on the market
        "material_usage": material_usage,
        "dependencies_needed": dependencies_needed,
        "inventory_savings": inventory_items_used,
        "expected_invention_materials_used": expected_invention,
        "invention_cost": invention_cost,

        # --- new fields
        "true_profit": true_profit,
        "total_revenue": revenue,
        "sales_fees": fees,
        "cash_profit": cash_profit,                   # revenue - fees - purchases - invention
        "stock_value_used": stock_value_used,
        "production_plan": production_plan,
        "units_produced": units_produced,
        "units_sold": units_sold,
        "shopping_list": shopping_list,
        "purchase_cost": purchase_cost,
        "purchase_volume": purchase_volume,           # m3 of everything on the shopping list
        "sales": sales,                               # per item: units, m3 and value to haul out
        "sell_volume": sell_volume,                   # m3 of everything sold
        "marginal_values": marginal_values,
        "settings": {"budget": budget, "fee": fee, "buy": buy_mode, "cargo_m3": cargo_m3,
                     "cargo_buy": cargo_buy, "cargo_sell": cargo_sell},
        "solver_status": status,
        "warnings": warnings,
    }
    return result, 200
