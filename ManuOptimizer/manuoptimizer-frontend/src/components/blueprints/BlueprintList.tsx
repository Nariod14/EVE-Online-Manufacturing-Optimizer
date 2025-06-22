"use client";
import { useEffect, useState } from "react";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Pencil, Trash2, RotateCcw, ChevronDown, ChevronUp } from "lucide-react";
import type { Blueprint, BlueprintT2, BlueprintTier } from "@/types/blueprints";
import { useMswReady } from "@/hooks/useMswReady";
import { Material } from "@/types/materials";
import { CardContent, CardDescription } from "../ui/card";
import { ConfirmDeleteButton } from "../utils/utils";
import { numberToWords } from "../utils/utils";



type SortKey =
  | "name"
  | "sell_price"
  | "material_cost"
  | "full_material_cost"
  | "profit"
  | "profit_percent"
  | "station_name"
  | "max"
  | "invention_chance";


type SortState = {
  key: SortKey;
  direction: "asc" | "desc";
};

function formatIsk(n: number) {
  return n.toLocaleString() + " ISK";
}


function MaterialsCell({ materials }: { materials: Material[] }) {
  if (!materials || materials.length === 0) {
    return <div className="text-gray-400 italic">No materials</div>;
  }

  const grouped = materials.reduce<Record<string, Record<string, number>>>((acc, mat) => {
    if (!mat) return acc; // <-- This line prevents the crash!
    const category = mat.category || "Other";
    if (!acc[category]) acc[category] = {};
    acc[category][mat.name] = mat.quantity;
    return acc;
  }, {});


  return (
    <ul className="list-none pl-0 m-0 text-xs">
      {Object.entries(grouped).map(([category, items]) => (
        <li key={category}>
          <span className="font-semibold">{category}</span>
          <ul className="list-none pl-3">
            {Object.entries(items).map(([item, qty]) => (
              <li key={item}>
                <span className="text-accent">{item}</span>: {qty}
              </li>
            ))}
          </ul>
        </li>
      ))}
    </ul>
  );
}


type BlueprintsListProps = {
  blueprints: Blueprint[];
  onEdit?: (bp: Blueprint, tier: "T1" | "T2") => void;
  onSetBlueprints?: React.Dispatch<React.SetStateAction<Blueprint[]>>;
  loading?: boolean;
  fetchBlueprints?: () => Promise<Blueprint[]>
};

export default function BlueprintsList({
  blueprints,
  onEdit,
  onSetBlueprints,
  loading,
  fetchBlueprints
}: BlueprintsListProps) {
  const [maxEdits, setMaxEdits] = useState<Record<number, string>>({});
  const [resettingAll, setResettingAll] = useState<{ [tier in BlueprintTier]?: boolean }>({});

  // Sorting state per tier
  const [t1Sort, setT1Sort] = useState<SortState>({ key: "name", direction: "asc" });
  const [t2Sort, setT2Sort] = useState<SortState>({ key: "name", direction: "asc" });

  const [searchQuery, setSearchQuery] = useState("");


  const mswReady = useMswReady();

  useEffect(() => {
    fetchBlueprints?.();
  }, []);


  function bpTierCheck(bp: Blueprint): bp is BlueprintT2 {
    return bp.tier === "T2";
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this blueprint?")) return;

    const res = await fetch(`/api/blueprints/blueprint/${id}`, { method: "DELETE" });

    if (res.ok) {
      toast.success("Blueprint deleted");
      fetchBlueprints?.();
    } else {
      toast.error("Failed to delete blueprint");
    }
  };

  const handleResetMax = async (id: number) => {
    if (!onSetBlueprints) return;

    console.log("Resetting max value for blueprint", id);

    const res = await fetch(`/api/blueprints/blueprint/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ max: null }),
    });

    if (res.ok) {
      onSetBlueprints((prev) =>
        prev.map((bp) => (bp.id === id ? { ...bp, max: null } : bp))
      );

      setMaxEdits((prev) => {
        const newEdits = { ...prev };
        delete newEdits[id];
        return newEdits;
      });

      console.log("Toast triggered for individual reset");
      toast.success("Blueprint max value reset");
    } else {
      console.error("Failed to reset max value: " + res.statusText);
      toast.error("Failed to reset max value");
    }
  };

  const handleResetAllMax = async (tier: BlueprintTier) => {
    if (!onSetBlueprints) return;

    setResettingAll((prev) => ({ ...prev, [tier]: true }));
    console.log("Resetting all max values for tier", tier);

    const res = await fetch("/api/blueprints/blueprints/reset_max", {
      method: "POST",
    });

    if (res.ok) {
      console.log("All max values reset");
      toast.success("All max values reset");

      onSetBlueprints((prev) =>
        prev.map((bp) => ({
          ...bp,
          max: null,
        }))
      );

      setMaxEdits({});
    } else {
      console.error("Failed to reset all max values" + res.statusText);
      toast.error("Failed to reset all max values");
    }

    setResettingAll((prev) => ({ ...prev, [tier]: false }));
  };

  const handleMaxInput = (id: number, value: string) => {
    setMaxEdits((prev) => ({ ...prev, [id]: value }));
  };
  const handleMaxBlur = async (id: number) => {
    const value = maxEdits[id];
    if (value === "" || value == null) return;
    const parsed = parseInt(value, 10);
    if (isNaN(parsed)) return;
    const res = await fetch(`/api/blueprints/blueprint/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ max: parsed }),
    });
    if (res.ok) {
      toast.success("Max value updated");
    
    } else {
      toast.error("Failed to update max value");
    }
  };

  // Sorting helpers
function sortBlueprints(arr: Blueprint[], sort: SortState) {
  return [...arr].sort((a, b) => {
    const dir = sort.direction === "asc" ? 1 : -1;
    switch (sort.key) {
      case "name":
        return a.name.localeCompare(b.name) * dir;
      case "sell_price":
        return (a.sell_price - b.sell_price) * dir;
      case "material_cost":
        return (a.material_cost - b.material_cost) * dir;
      case "full_material_cost":
        // Only T2 blueprints have this field
        const aCost = a.tier === "T2" ? a.full_material_cost : a.material_cost;
        const bCost = b.tier === "T2" ? b.full_material_cost : b.material_cost;
        return (aCost - bCost) * dir;
      case "profit":
        const aProfit = a.sell_price - (a.tier === "T2" ? a.full_material_cost : a.material_cost);
        const bProfit = b.sell_price - (b.tier === "T2" ? b.full_material_cost : b.material_cost);
        return (aProfit - bProfit) * dir;
      case "profit_percent": {
        const aCost = a.tier === "T2" ? a.full_material_cost : a.material_cost;
        const bCost = b.tier === "T2" ? b.full_material_cost : b.material_cost;

        const aPct = aCost > 0 ? ((a.sell_price - aCost) / aCost) * 100 : 0;
        const bPct = bCost > 0 ? ((b.sell_price - bCost) / bCost) * 100 : 0;

        return (aPct - bPct) * dir;
      }
      case "station_name":
      return (
        (a.station?.name || a.station_name || "Jita 4-4").localeCompare(
          b.station?.name || b.station_name || "Jita 4-4"
        ) * dir
      );
      case "max":
        return ((a.max ?? 0) - (b.max ?? 0)) * dir;
      case "invention_chance":
        // Only T2 blueprints have this field
        const aChance = a.tier === "T2" ? a.invention_chance : 0;
        const bChance = b.tier === "T2" ? b.invention_chance : 0;
        return (aChance - bChance) * dir;
      default:
        return 0;
    }
  });
}


function filterBlueprints(bpList: Blueprint[], query: string): Blueprint[] {
  const lower = query.trim().toLowerCase();
  if (!lower) return bpList;

  return bpList.filter((bp) => {
    const sellPrice = bp.sell_price;
    const materialCost = bp.material_cost;

    const baseProfit = sellPrice - materialCost;
    const baseProfitPct =
      materialCost > 0 ? ((baseProfit / materialCost) * 100).toFixed(2) : "-";

    const baseMatch =
      bp.name?.toLowerCase().includes(lower) ||
      bp.station_name?.toLowerCase().includes(lower) ||
      String(sellPrice).includes(lower) ||
      String(materialCost).includes(lower) ||
      String(baseProfit).includes(lower) ||
      baseProfitPct.includes(lower) ||
      String(bp.max ?? "").includes(lower);

    // Match against materials (names and optional quantities)
    const materialsMatch = Array.isArray(bp.materials)
      ? bp.materials.some((mat) => {
          return (
            mat.name?.toLowerCase().includes(lower) ||
            String(mat.quantity).includes(lower)
          );
        })
      : false;

    if (bp.tier === "T2") {
      const t2 = bp as BlueprintT2;
      const fullProfit = sellPrice - t2.full_material_cost;
      const fullProfitPct =
        t2.full_material_cost > 0
          ? ((fullProfit / t2.full_material_cost) * 100).toFixed(2)
          : "-";

      const t2Match =
        String(t2.full_material_cost).includes(lower) ||
        String(t2.invention_chance).includes(lower) ||
        String(fullProfit).includes(lower) ||
        fullProfitPct.includes(lower);

      return baseMatch || t2Match || materialsMatch;
    }

    return baseMatch || materialsMatch;
  });
}




  // Split by tier
  const t1Blueprints = blueprints.filter((b) => b.tier === "T1");
  const t2Blueprints = blueprints.filter(bpTierCheck);

  const filteredT1 = filterBlueprints(t1Blueprints, searchQuery);
  const filteredT2 = filterBlueprints(t2Blueprints, searchQuery);


  // Table headers config
// Allow any string for key, but only SortKey values are sortable
    const t1Headers: { key: string; label: string }[] = [
        { key: "name", label: "Name" },
        { key: "sell_price", label: "Sell Price" },
        { key: "material_cost", label: "Material Cost" },
        { key: "materials", label: "Materials" }, // not sortable
        { key: "profit", label: "Profit %" },
        { key: "station_name", label: "Station" },
        { key: "max", label: "Max" },
        { key: "actions", label: "Actions" }, // not sortable
    ];
    
    const t2Headers: { key: string; label: string }[] = [
        { key: "name", label: "Name" },
        { key: "invention_chance", label: "Invention Chance %" },
        { key: "sell_price", label: "Sell Price" },
        { key: "full_material_cost", label: "Full Material Cost" },
        { key: "materials", label: "Materials" }, // not sortable
        { key: "profit", label: "Profit %" },
        { key: "station_name", label: "Station" },
        { key: "max", label: "Max" },
        { key: "actions", label: "Actions" }, // not sortable
      ];
      
  // Table renderers
function renderHeader(
  headers: { key: string; label: string }[],
  sort: SortState,
  tier: "T1" | "T2",
  setSort: (s: SortState) => void
) {
  return (
    <tr className={tier === "T2" ? "text-orange-400" : "text-blue-400"}>
      {headers.map((h) => {
        // Only allow sorting if the key is in SortKey
        const isSortable = [
          "name",
          "sell_price",
          "material_cost",
          "full_material_cost",
          "profit",
          "station_name",
          "max",
          "invention_chance",
        ].includes(h.key);

        const isSorted = sort.key === h.key;

        return (
          <th
            key={h.key}
            className={`py-2 px-3 text-left ${
              isSortable ? "cursor-pointer select-none hover:underline" : ""
            }`}
            onClick={() =>
              isSortable &&
              setSort({
                key: h.key as SortKey,
                direction: isSorted && sort.direction === "asc" ? "desc" : "asc",
              })
            }
          >
            <span className="flex items-center gap-1">
              {h.label}
              {isSortable && isSorted ? (
                sort.direction === "asc" ? (
                  <ChevronDown className="w-4 h-4 inline" />
                ) : (
                  <ChevronUp className="w-4 h-4 inline" />
                )
              ) : null}
            </span>
          </th>
        );
      })}
    </tr>
  );
}


  return (
    <CardContent>
      <CardDescription>
        <div className="mb-4 flex justify-between items-center gap-4">
          <Input
            type="text"
            placeholder="Search blueprints..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full max-w-md bg-blue-900 text-blue-200 border-blue-700"
          />
        </div>
      </CardDescription>
          <Accordion type="multiple" className="mb-4">
            {/* T1 Section */}
            <AccordionItem value="t1" defaultChecked>
              <AccordionTrigger
                className="text-lg font-semibold text-blue-100 bg-gradient-to-r from-blue-800 via-blue-700 to-blue-900 hover:no-underline rounded-t-xl px-4 py-3"
                style={{
                  borderBottom: "2px solid #60a5fa",
                  boxShadow: "0 2px 8px 0 #2563eb22",
                }}
              >
                <span className="text-blue-200">Tier 1 Blueprints</span>
              </AccordionTrigger>
              <AccordionContent className="bg-gradient-to-br from-blue-950 via-blue- to-slate-950 hover:no-underline rounded-b-xl px-2 pb-4 pt-2">
                { filteredT1.length ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm bg-blue-950/70 rounded-xl shadow">
                      <thead>{renderHeader(t1Headers, t1Sort, "T1", setT1Sort)}</thead>
                      <tbody>
                        {sortBlueprints(filteredT1, t1Sort).map((bp) => {
                          const sellPrice = Math.round(bp.sell_price);
                          const materialCost = Math.round(bp.material_cost);
                          const profit = sellPrice - materialCost;
                          const profitPct =
                            materialCost > 0
                              ? ((profit / materialCost) * 100).toFixed(2)
                              : "-";
                          return (
                            <tr
                              key={bp.id}
                              className="border-b border-blue-800 hover:bg-blue-900/60 text-blue-200 transition"
                            >
                              <td className="py-2 px-3 font-semibold">{bp.name}</td>
                              <td className="py-2 px-3">
                                {formatIsk(sellPrice)}{" "}
                                <span className="text-xs text-blue-400 ml-1">
                                  ({numberToWords(sellPrice)} isk)
                                </span>
                                {bp.used_jita_fallback && (
                                  <span
                                    className="ml-2 text-orange-400"
                                    title="Fallback to Jita pricing"
                                  >
                                    &#9888;
                                  </span>
                                )}
                              </td>
                              <td className="py-2 px-3">
                                {formatIsk(materialCost)}{" "}
                                <span className="text-xs text-blue-400 ml-1">
                                  ({numberToWords(materialCost)} isk)
                                </span>
                              </td>
                              <td className="py-2 px-3">
                                <MaterialsCell materials={bp.materials} />
                              </td>
                              <td className="py-2 px-3 text-center">{profitPct}%</td>
                              <td className="py-2 px-3 text-center">
                                {bp.station_name || bp.station?.name || "Jita 4-4"}
                              </td>
                              <td className="py-2 px-3 text-center">
                                <Input
                                  type="number"
                                  value={maxEdits[bp.id] ?? (bp.max ?? "")}
                                  onChange={(e) =>
                                    handleMaxInput(bp.id, e.target.value)
                                  }
                                  onBlur={() => handleMaxBlur(bp.id)}
                                  className="w-16 text-center bg-blue-900 border-blue-700"
                                />
                              </td>
                              <td className="py-2 px-3 text-center">
                                <div className="flex flex-col gap-2 items-stretch">
                                  <Button
                                    size="sm"
                                    variant="secondary"
                                    className="bg-blue-700 text-white"
                                    onClick={() => onEdit?.(bp, "T1")}
                                  >
                                    <Pencil className="w-4 h-4 mr-1" /> Edit
                                  </Button>

                                  <ConfirmDeleteButton onDelete={() => handleDelete(bp.id)}>
                                    <Trash2 className="w-4 h-4 mr-1" /> Delete
                                  </ConfirmDeleteButton>
                                  
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="border-blue-500 text-blue-700 bg-blue-200"
                                    onClick={() => handleResetMax(bp.id)}
                                  >
                                    <RotateCcw className="w-4 h-4 mr-1" /> Reset Max
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                    <div className="flex justify-end mt-3">
                      <Button
                        variant="outline"
                        className="border-blue-500 text-blue-700 bg-blue-50"
                        onClick={() => handleResetAllMax("T1")}
                        disabled={!!resettingAll["T1"]}
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        {resettingAll["T1"] ? "Resetting..." : "Reset All Max Values"}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-blue-400">No Tier 1 blueprints found.</div>
                )}
              </AccordionContent>
            </AccordionItem>
            {/* T2 Section */}
            <AccordionItem value="t2">
              <AccordionTrigger
                className="text-lg font-semibold bg-gradient-to-r from-orange-400 via-orange-500 to-yellow-500 text-orange-900 hover:no-underline rounded-t-xl px-4 py-3"
                style={{
                  borderBottom: "2px solid #f59e42",
                  boxShadow: "0 2px 8px 0 #f59e4222",
                }}
              >
                <span className="text-[#fcf2e2]">Tier 2 Blueprints</span>

                </AccordionTrigger>

                <AccordionContent className="bg-[#2d1e13] rounded-b-xl px-2 pb-4 pt-2 border-l-[8px] border-[#ff9800] shadow-[0_4px_20px_0_rgba(200,120,30,0.13)]">

                {filteredT2.length ? (
                    <div className="overflow-x-auto">
                    <table className="min-w-full text-sm bg-[#2d1e13] rounded-xl shadow">
                        <thead>{renderHeader(t2Headers, t2Sort, "T2", setT2Sort)}</thead>
                        <tbody>
                          {sortBlueprints(filteredT2, t2Sort).map((bp) => {
                            if (bpTierCheck(bp)) {
                                const materialCost = Math.round(bp.material_cost);
                                const sellPrice = Math.round(bp.sell_price);
                                const fullMaterialCost = Math.round(bp.full_material_cost ?? bp.material_cost);
                                const profit = sellPrice - fullMaterialCost;
                                const profitPct = fullMaterialCost > 0
                                ? ((profit / fullMaterialCost) * 100).toFixed(2)
                                : "-";

                                return (
                                <tr
                                    key={bp.id}
                                    className="border-b border-[#ff9800] hover:bg-[#5a492f] text-amber-100 transition"
                                >
                                    <td className="py-2 px-3 font-semibold text-[#e8d5b9]">{bp.name}</td>
                                    <td className="py-2 px-3 text-center text-[#fff1dc]">
                                    {bp.invention_chance != null
                                        ? (bp.invention_chance * 100).toFixed(1) + "%"
                                        : "-"}
                                    </td>
                                    <td className="py-2 px-3 text-[#ffedd1]">
                                    {formatIsk(sellPrice)}{" "}
                                    <span className="text-xs text-[#d57d00] ml-1">
                                        ({numberToWords(sellPrice)} isk)
                                    </span>
                                    {bp.used_jita_fallback && (
                                        <span className="ml-2 text-[#d57d00]" title="Fallback to Jita pricing">
                                        &#9888;
                                        </span>
                                    )}
                                    </td>
                                    <td className="py-2 px-3 text-[#ffedd1]">
                                    {formatIsk(fullMaterialCost)}{" "}
                                    <span className="text-xs text-[#d57d00] ml-1">
                                        ({numberToWords(fullMaterialCost)} isk)
                                    </span>
                                    </td>
                                    <td className="py-2 px-3">
                                    <MaterialsCell materials={bp.materials} />
                                    </td>
                                    <td className="py-2 px-3 text-center text-[#ffeed4]">{profitPct}%</td>
                                    <td className="py-2 px-3 text-center text-[#ffedd1]">
                                    {bp.station_name || bp.station?.name || "Jita 4-4"}
                                    </td>
                                    <td className="py-2 px-3 text-center">
                                    <Input
                                        type="number"
                                        value={maxEdits[bp.id] ?? (bp.max ?? "")}
                                        onChange={(e) => handleMaxInput(bp.id, e.target.value)}
                                        onBlur={() => handleMaxBlur(bp.id)}
                                        className="w-16 text-center bg-[#3a2719] border-[#e08900] text-[##ffedd1]"
                                    />
                                    </td>
                                    <td className="py-2 px-3 text-center">
                                    <div className="flex flex-col gap-2 items-stretch">
                                      <Button
                                        size="sm"
                                        variant="secondary"
                                        className="bg-[#e08900] text-white hover:bg-[#f09a00]"
                                        onClick={() => onEdit?.(bp, "T2")}
                                      >
                                        <Pencil className="w-4 h-4 mr-1" /> Edit
                                      </Button>

                                        <ConfirmDeleteButton onDelete={() => handleDelete(bp.id)}>
                                          <Trash2 className="w-4 h-4 mr-1" /> Delete
                                        </ConfirmDeleteButton>
                                        <Button
                                        size="sm"
                                        variant="outline"
                                        className="border-[#e08900] text-[#bf7404] bg-amber-100"
                                        onClick={() => handleResetMax(bp.id)}
                                        >
                                        <RotateCcw className="w-4 h-4 mr-1" /> Reset Max
                                        </Button>
                                    </div>
                                    </td>
                                </tr>
                                );
                              } else {
                                console.log(`Blueprint ${bp.id} is not Tier 2!`);
                                return null;
                              }
                            })}
                            </tbody>
                        </table>

                        <div className="flex justify-end mt-3">
                            <Button
                            variant="outline"
                            className="border-[#e08900] text-[#ce7c00] bg-amber-50"
                            onClick={() => handleResetAllMax("T2")}
                            disabled={!!resettingAll["T2"]}
                            >
                            <RotateCcw className="w-4 h-4 mr-2" />
                            {resettingAll["T2"] ? "Resetting..." : "Reset All Max Values"}
                            </Button>
                        </div>
                        </div>
                    ) : (
                        <div className="p-6 text-[#d57d00]">No Tier 2 blueprints found.</div>
                    )}
                    </AccordionContent>

                </AccordionItem>
              </Accordion>
              <div className="price-legend mt-2 text-sm text-[#ff9500]">
                <span className="text-orange-400">&#9888;</span> Fallback to Jita pricing
              </div>
            </CardContent>
      );
      

}
