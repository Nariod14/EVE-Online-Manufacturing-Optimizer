export type InventorySavings = Record<
  string,
  {
    amount: number;
    category?: string;
  }
>;


export type OptimizeResponse = {
  inventory_savings: InventorySavings;
  total_profit: number;
  true_profit_jita: number;
  true_profit_inventory: number;
  dependencies_needed: Record<string, number>;
  what_to_produce: Record<string, number>;
  material_usage: Record<
    string,
    {
      used: number;
      remaining: number;
      category?: string;
    }
  >;
};

export const mockOptimizeResponse: OptimizeResponse = {
  total_profit: 420000000,
  true_profit_jita: 278000000,
  true_profit_inventory: 314000000,
  dependencies_needed: {
    "R.A.M. Energy Tech": 10,
    "Morphite Coolant Tube": 5,
    "Thruster Console": 8,
  },
  what_to_produce: {
    "Warp Core Stabilizer II": 14,
    "Hobgoblin II": 20,
    "Knobbgoblin I": 999,
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
    "Tritanium": { amount: 10000, category: "Minerals" },
    "Pyerite": { amount: 5000, category: "Minerals" },
    "Coherent Asteroid Mining Crystal Type A I": { amount: 100, category: "Items" },
    "Coolant": { amount: 50, category: "Planetary Materials" },
    "Hydrogen Batteries": { amount: 300, category: "Fuel" },
    "RAM Electronics": { amount: 5, category: "Components" },
    "Nanomechanical Microprocessor": { amount: 12, category: "Reaction Materials" },
    "Unknown Goo": { amount: 999, category: "Other" },
  },
};

