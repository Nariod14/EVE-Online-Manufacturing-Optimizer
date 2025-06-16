import { Blueprint } from "./blueprints";
import { mockMaterials } from "./materials";

export const mockStations = [
  {
    id: 1,
    name: "Amarr VIII (Oris) - Emperor Family Academy",
    station_id: 60003760,
    blueprints: [
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
      }
    ]
  },
  {
    id: 2,
    name: "Jita IV - Moon 4 - Caldari Navy Assembly Plant",
    station_id: 60011866,
    blueprints: [
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
      }
    ]
  },
  {
    id: 3,
    name: "Rens VI - Moon 8 - Brutor Tribe Treasury",
    station_id: 60004588,
    blueprints: []
  },
  {
    id: 4,
    name: "Dodixie IX - Moon 20 - Federation Navy Assembly Plant",
    station_id: 60005686,
    blueprints: [
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
    ]
  }
];

export type Station = {
    id: number;
    name: string;
    station_id: number;
    blueprints?: Blueprint[]; // Optional
  };