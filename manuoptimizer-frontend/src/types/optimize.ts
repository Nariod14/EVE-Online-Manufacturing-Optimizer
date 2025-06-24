export type OptimizeResponse = {
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
  true_profit_jita: 278000000,          // Profit if you bought all materials at Jita
  true_profit_inventory: 314000000,     // Profit accounting for your inventory (example value)
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
    "Tritanium": { used: 500000, remaining: 100000, category: "Minerals" },
    "Pyerite": { used: 250000, remaining: -50000, category: "Minerals" },
    "Mexallon": { used: 150000, remaining: 20000, category: "Minerals" },
    "Data Interface": { used: 15, remaining: 5, category: "Invention Materials" },
    "RAM Electronics": { used: 10, remaining: -5, category: "Components" },
    "Zydrine": { used: 45000, remaining: 0, category: "Minerals" },
    "R.A.M. Energy Tech": { used: 10, remaining: 0, category: "Components" },
    "Coolant": { used: 100, remaining: -40, category: "Planetary Materials" },
    "Hydrogen Batteries": { used: 200, remaining: 300, category: "Fuel" },
    "Nanoelectrical Microprocessor": { used: 50, remaining: 5, category: "Reaction Materials" },
  },
};

