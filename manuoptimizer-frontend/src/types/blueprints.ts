import { Station } from "./stations";
import { Material, mockMaterials } from "./materials";
import { mockStations } from "./stations";
import { mock } from "node:test";

export type BlueprintTier = "T1" | "T2";

export type BlueprintBase = {
  id: number;
  type_id?: number | null;
  name: string;
  amt_per_run: number;
  materials: any; // JSON data
  sell_price: number;
  max?: number | null;
  material_cost: number;
  tier: BlueprintTier;
  station_id?: number | null;
  region_id: number;
  use_jita_sell: boolean;
  used_jita_fallback: boolean;
  station?: Station;
  // This is for display only, not in DB, but backend can add it for you
  station_name?: string;
};

export type BlueprintT2 = BlueprintBase & {
  tier: "T2";
  invention_chance: number;
  invention_cost: number;
  full_material_cost: number;
  runs_per_copy: number;
};

export type BlueprintT1 = BlueprintBase & {
  tier: "T1";
};

export type Blueprint = BlueprintT1 | BlueprintT2;

export const mockBlueprints = [
  {
    id: 1,
    name: "Hobgoblin I",
    type_id: 1001,
    amt_per_run: 1,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
      mockMaterials[2], // Mexallon
    ],
    sell_price: 1200000,
    max: null,
    material_cost: 900000,
    tier: "T1" as const,
    station_id: 60011866, // Jita
    region_id: 10000002,
    use_jita_sell: true,
    used_jita_fallback: true,
  },
  {
    id: 2,
    name: "Warp Core Stabilizer I",
    type_id: 1002,
    amt_per_run: 1,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
      mockMaterials[4], // Morphite
    ],
    sell_price: 500000,
    max: null,
    material_cost: 400000,
    tier: "T1" as const,
    station_id: 60003760, // Amarr
    region_id: 10000002,
    use_jita_sell: true,
    used_jita_fallback: true,
  },
  {
    id: 3,
    name: "Hobgoblin II",
    type_id: 2001,
    amt_per_run: 1,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
      mockMaterials[2], // Mexallon
      mockMaterials[5], // Advanced Drone Structure
    ],
    sell_price: 6200000,
    max: null,
    material_cost: 4100000,
    tier: "T2" as const,
    station_id: 60011866, // Jita
    region_id: 10000002,
    use_jita_sell: true,
    used_jita_fallback: true,
    invention_chance: 0.45,
    invention_cost: 950000,
    full_material_cost: 5200000,
    runs_per_copy: 10,
  },
  {
    id: 4,
    name: "Warp Core Stabilizer II",
    type_id: 2002,
    amt_per_run: 1,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
      mockMaterials[4], // Morphite
      mockMaterials[5], // Advanced Drone Structure
    ],
    sell_price: 15000000,
    max: null,
    material_cost: 10000000,
    tier: "T2" as const,
    station_id: 60005686, // Dodixie
    region_id: 10000002,
    use_jita_sell: true,
    used_jita_fallback: true,
    invention_chance: 0.32,
    invention_cost: 1100000,
    full_material_cost: 12500000,
    runs_per_copy: 10,
  },
  {
    id: 5,
    name: "R.A.M Energy Tech",
    type_id: 1003,
    amt_per_run: 100,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
    ],
    sell_price: 100000,
    max: null,
    material_cost: 50000,
    tier: "T1" as const,
    station_id: 60004588, // Rens
    region_id: 10000002,
    use_jita_sell: true,
    used_jita_fallback: true,
  },
];
