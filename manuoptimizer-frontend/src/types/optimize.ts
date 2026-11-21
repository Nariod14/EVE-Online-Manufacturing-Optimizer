export type InventorySavings = Record<
  string,
  {
    amount: number;
    category?: string;
  }
>;


// One row of the production plan: what to install and what comes out of it
export type ProductionPlanRow = {
  name: string;
  tier: string;
  runs: number;
  units_per_run: number;
  units_produced: number;
  units_sold: number;
  units_for_other_builds: number;
  revenue: number;
};

export type ShoppingListEntry = {
  quantity: number;
  unit_price: number;
  cost: number;
  category?: string;
  volume_m3?: number | null; // m3 of this line; null = volume unknown
};

// One item the plan sells, for hauling it out
export type SaleLine = {
  name: string;
  units: number;
  unit_volume: number | null; // m3 per unit; null = unknown
  volume_m3: number | null;
  value: number;              // units x sell price, before fees
};

// What one more unit of a material would add to the plan, next to what it costs
export type MarginalValue = {
  name: string;
  category?: string;
  value: number;
  market_price: number;
  ratio: number;
};

// "list" = only what is on the buy list (GET/PUT /api/buylist)
export type BuyMode = "none" | "list" | "all";

// GET /api/buylist/candidates
export type BuyListCandidate = {
  name: string;
  category: string;
  sell_price: number | null;
  in_stock: number;
  on_list: boolean;
};

export type BuyListItem = {
  name: string;
  type_id: number | null;
  sell_price: number | null;
};

// PUT /api/buylist
export type BuyListSaveResponse = {
  items: BuyListItem[];
  unknown: string[];   // not found in the SDE, not added
  no_price: string[];  // added, no market price yet
};

export type OptimizeSettings = {
  budget: number;
  fee: number; // fraction: 0.05 = 5%
  buy: BuyMode;
  cargo_m3?: number | null; // m3 limit (capacity x trips); null = no limit
  cargo_buy?: boolean;      // limit applied to purchases
  cargo_sell?: boolean;     // limit applied to sales
};

export type OptimizeResponse = {
  expected_invention_materials_used: Record<string, number>;
  invention_cost: number;
  inventory_savings: InventorySavings;
  total_profit: number;
  true_profit_jita: number;
  true_profit_inventory: number;
  dependencies_needed: Record<string, number>;
  what_to_produce: Record<string, number>;
  original_production_plan: Record<string, number>; // New field for original production plan
  adjusted_production_plan: Record<string, number>; // New field for adjusted production plan
  material_usage: Record<
    string,
    {
      used: number;
      remaining: number;
      category?: string;
      bought?: number;
    }
  >;

  // Added with the reworked optimizer. Optional so an older backend still type-checks.
  true_profit?: number;
  total_revenue?: number;
  sales_fees?: number;
  purchase_cost?: number;
  purchase_volume?: number; // m3 of the shopping list
  sales?: SaleLine[];
  sell_volume?: number;     // m3 of everything sold
  cash_profit?: number;
  stock_value_used?: number;
  inventory_cost_savings?: number;
  production_plan?: ProductionPlanRow[];
  units_produced?: Record<string, number>;
  units_sold?: Record<string, number>;
  shopping_list?: Record<string, ShoppingListEntry>;
  marginal_values?: MarginalValue[];
  settings?: OptimizeSettings;
  solver_status?: string;
  warnings?: string[];
};


export const mockOptimizeResponse: OptimizeResponse = {
  total_profit: 420000000,
  true_profit_jita: 278000000,
  invention_cost: 50000000,
  true_profit_inventory: 314000000,
  dependencies_needed: {
    "R.A.M. Energy Tech": 10,
    "Morphite Coolant Tube": 5,
    "Thruster Console": 8,
  },
  what_to_produce: {
    "Warp Core Stabilizer II": 14,
    "Hobgoblin II": 20,
    "Warp Core Stabilizer I": 999,
  },
  original_production_plan: { // New field for original production plan
    "Warp Core Stabilizer II": 14,
    "Hobgoblin II": 20,
    "Knobbgoblin I": 999,
  },
  adjusted_production_plan: { // New field for adjusted production plan
    "Warp Core Stabilizer II": 1, // Example adjusted value after inventory consumption
    "Hobgoblin II": 20,
    // "Warp Core Stabilizer I": 999,
    // // "test1": 69,
  },
  material_usage: {
    // 0% (unused)
    "Useless Scrap": { used: 0, remaining: 1000, category: "Other" },

    // 10% (low usage)
    "Scordite": { used: 100, remaining: 900, category: "Minerals" },

    // 35% (below green threshold)
    "Plagioclase": { used: 350, remaining: 650, category: "Minerals" },

    // 60% (light green zone)
    "Mexallon": { used: 600, remaining: 400, category: "Minerals" },

    // 85% (yellow zone)
    "Pyerite": { used: 850, remaining: 150, category: "Minerals" },

    // 100% (perfect match)
    "Isogen": { used: 1000, remaining: 0, category: "Minerals" },

    // 110% (minor overuse)
    "Zydrine": { used: 1100, remaining: -100, category: "Minerals" },

    // 130% (orange/red zone)
    "Megacyte": { used: 1300, remaining: -300, category: "Minerals" },

    // 160% (heavy overuse)
    "Nocxium": { used: 1600, remaining: -600, category: "Minerals" },

    // 205% (severe overuse)
    "Morphite": { used: 2050, remaining: -1050, category: "Minerals" },

    // Testing "Items" negative remaining (to be built)
    "Hobgoblin I": { used: 50, remaining: -10, category: "Items" },
    "Warp Core Stabilizer I": { used: 100, remaining: -40, category: "Items" },

    // Planetary
    "Coolant": { used: 500, remaining: -200, category: "Planetary Materials" },

    // Components
    "R.A.M. Robotics": { used: 25, remaining: -5, category: "Components" },

    // Fuel
    "Hydrogen Batteries": { used: 1000, remaining: 0, category: "Fuel" },

    // Invention
    "Data Interface": { used: 12, remaining: 3, category: "Invention Materials" },

    // Salvaged Materials
    "Burned Logic Circuit": { used: 200, remaining: -50, category: "Salvaged Materials" },

    // Reaction Materials
    "Fullerene Intercalated Sheets": { used: 140, remaining: 10, category: "Reaction Materials" },
  },
  
  inventory_savings: {
    // "Coherent Asteroid Mining Crystal Type A I": { amount: 100, category: "Items" },
    // "Hydrogen Batteries": { amount: 300, category: "Fuel" },
    // "R.A.M. Robotics": { amount: 25, category: "Components" },
  },

  expected_invention_materials_used: {
    "Data Interface": 12,
    "Datacore - Laser Physics": 2,
    "Datacore - Cryo Physics": 2,
    "Datacore - Thermal Physics": 2,
    "Datacore - Quantum Physics": 2,
    "Datacore - Gravity Physics": 2,
  },

  // Fields from the reworked optimizer
  sales_fees: 21000000,
  purchase_cost: 150000000,
  cash_profit: 199000000,
  production_plan: [
    { name: "Hobgoblin II", tier: "T2", runs: 20, units_per_run: 1, units_produced: 20, units_sold: 20, units_for_other_builds: 0, revenue: 20000000 },
    { name: "Warp Core Stabilizer I", tier: "T1", runs: 999, units_per_run: 1, units_produced: 999, units_sold: 985, units_for_other_builds: 14, revenue: 300000000 },
    { name: "Warp Core Stabilizer II", tier: "T2", runs: 14, units_per_run: 1, units_produced: 14, units_sold: 14, units_for_other_builds: 0, revenue: 100000000 },
  ],
  shopping_list: {
    "Nocxium": { quantity: 150000, unit_price: 800, cost: 120000000, category: "Minerals" },
    "Tritanium": { quantity: 7000000, unit_price: 4.2, cost: 29400000, category: "Minerals" },
  },
  marginal_values: [
    { name: "Nocxium", category: "Minerals", value: 1300, market_price: 800, ratio: 1.625 },
    { name: "Megacyte", category: "Minerals", value: 2400, market_price: 2000, ratio: 1.2 },
  ],
  settings: { budget: 150000000, fee: 0.05, buy: "list" },
  warnings: [],
};
