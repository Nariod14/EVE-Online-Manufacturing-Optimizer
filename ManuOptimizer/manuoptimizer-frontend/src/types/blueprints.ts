import { Station } from "./stations";
import { Material, mockMaterials } from "./materials";
import { mock } from "node:test";

export type BlueprintTier = "T1" | "T2";

export type BlueprintBase = {
  id: number;
  type_id?: number | null;
  name: string;
  materials: any; // JSON data
  sell_price: number;
  max?: number | null;
  material_cost: number;
  tier: "T1" | "T2";
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


// TypeScript type for reference
export const mockBlueprints: {
  id: number;
  name: string;
  tier: "T1" | "T2";
  sell_price: number;
  material_cost: number;
  full_material_cost?: number;
  used_jita_fallback: boolean;
  station_name?: string;
  max?: number | null;
  materials: Material[];
  invention_chance?: number | null;
}[] = [
  // T1 Example
  {
    id: 1,
    name: "Hobgoblin I",
    tier: "T1",
    sell_price: 1200000,
    material_cost: 900000,
    used_jita_fallback: false,
    station_name: "Jita IV - Moon 4",
    max: 10,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
      mockMaterials[2], // Mexallon
      mockMaterials[3] // Drone Structure
    ]
  },
  // T1 Example with Jita fallback
  {
    id: 2,
    name: "Warp Core Stabilizer I",
    tier: "T1",
    sell_price: 500000,
    material_cost: 400000,
    used_jita_fallback: true,
    station_name: "Amarr VIII (Oris)",
    max: null,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
      mockMaterials[4] // Morphite
    ]
  },
  // T2 Example
  {
    id: 3,
    name: "Hobgoblin II",
    tier: "T2",
    sell_price: 6200000,
    material_cost: 4100000,
    full_material_cost: 4700000,
    used_jita_fallback: false,
    station_name: "Jita IV - Moon 4",
    max: 5,
    invention_chance: 0.42,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
      mockMaterials[2], // Mexallon
      mockMaterials[3], // Drone Structure
      mockMaterials[5], // Morphite
      mockMaterials[6] // Advanced Drone Structure
    ]
  },
  // T2 Example with Jita fallback and no max
  {
    id: 4,
    name: "Warp Core Stabilizer II",
    tier: "T2",
    sell_price: 15000000,
    material_cost: 10000000,
    full_material_cost: 11000000,
    used_jita_fallback: true,
    station_name: "Dodixie IX - Moon 20",
    max: null,
    invention_chance: 0.355,
    materials: [
      mockMaterials[0], // Tritanium
      mockMaterials[1], // Pyerite
      mockMaterials[4], // Morphite
      mockMaterials[5] // Advanced Stabilizer
    ]
  }
];