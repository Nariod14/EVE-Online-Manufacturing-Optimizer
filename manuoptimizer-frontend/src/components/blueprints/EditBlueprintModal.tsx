"use client";
import * as React from "react";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Blueprint, BlueprintBase, BlueprintT1, BlueprintT2 } from "@/types/blueprints";
import { useEffect, useState } from "react";
import { BlueprintTier } from "@/types/blueprints";
import { Material } from "@/types/materials";

type EditBlueprintModalProps = {
  open: boolean;
  blueprint: Blueprint | null;
  tier: "T1" | "T2" | null
  onClose: () => void;
  onSave: (bp: import('@/types/blueprints').Blueprint) => void;
};

export function EditBlueprintModal({
  open,
  blueprint,
  tier,
  onClose,
  onSave,
}: EditBlueprintModalProps) {
  const [form, setForm] = React.useState<Blueprint | null>(null);
  const modalClassName = tier === "T1"
  ? "bg-gradient-to-br from-blue-900 via-blue-800 to-blue-700 text-blue-100"
  : tier === "T2"
  ? "bg-gradient-to-br from-orange-800 via-orange-700 to-yellow-700 text-orange-100"
  : "";
  const [stations, setStations] = useState<{ station_id: string; name: string }[]>([]);
  const [category, setCategory] = useState<string>("");
  const [isCustom, setIsCustom] = useState(false);
  const [amtPerRun, setAmtPerRun] = useState<number>(1);
  const [customAmtPerRun, setCustomAmtPerRun] = useState<number | undefined>(undefined);

  // State for manual category text input when "Other" is selected
  const [manualCategory, setManualCategory] = useState<string>("");

  useEffect(() => {
    async function fetchStations() {
      try {
        const res = await fetch("/api/stations");
        const data = await res.json();
        setStations(data);
      } catch (err) {
        console.error("Failed to fetch stations:", err);
      }
    }
    if (open) fetchStations();
  }, [open]);


  useEffect(() => {
    if (blueprint) setForm(blueprint);
  }, [blueprint]);

  if (!form) return null;

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    const { name, value } = e.target;
    setForm((prev) =>
      prev
        ? {
            ...prev,
            [name]:
              name === "sell_price" || name === "material_cost"
                ? parseFloat(value)
                : value,
          }
        : prev
    );
  }

function handleTierChange(value: "T1" | "T2") {
  setForm((prev) => {
    if (!prev) return prev;

    // Handle T2 conversion
    if (value === "T2") {
      // For T1 → T2 conversion
      if (prev.tier === "T1") {
        return {
          ...prev,
          tier: "T2",
          invention_chance: 0,
          invention_cost: 0,
          full_material_cost: prev.material_cost,
          runs_per_copy: 10,
        } as BlueprintT2;
      }
      // For T2 → T2 (no change needed)
      return prev as BlueprintT2;
    } 
    // Handle T1 conversion
    else {
      // For T2 → T1 conversion
      if (prev.tier === "T2") {
        const { 
          invention_chance, 
          invention_cost, 
          full_material_cost, 
          runs_per_copy, 
          ...baseProps 
        } = prev;
        return {
          ...baseProps,
          tier: "T1",

        } as BlueprintT1;
      }
      // For T1 → T1 (no change needed)
      return prev as BlueprintT1;
    }
  });
}

function onSaveLocal(updated: Blueprint) {
  for (const mat of updated.materials || []) {
    if (!mat.category || mat.category.trim() === "") {
      alert(`Please select or enter a category for material: ${mat.name || "Unnamed"}`);
      return; // stops saving if any category invalid
    }
    
  }
  // All good, call parent's onSave
  onSave(updated);
}






 function handleInventionChanceChange(e: React.ChangeEvent<HTMLInputElement>) {
  const value = e.target.value;
  setForm((prev) =>
    prev && prev.tier === "T2"
      ? {
          ...prev,
          invention_chance: value ? parseFloat(value) / 100 : 0,
        }
      : prev
  );
}


  function handleRunsPerCopyChange(value: string) {
    setForm((prev) =>
      prev ? { ...prev, runs_per_copy: parseInt(value, 10) } : prev
    );
  }

  function updateMaterialField(index: number, field: keyof Material, value: any) {
  setForm((prev) => {
    if (!prev) return null; // fallback safety for null

    const updatedMaterials = [...(prev.materials || [])];
    updatedMaterials[index] = {
      ...updatedMaterials[index],
      [field]: value,
    };

    return {
      ...prev,
      materials: updatedMaterials,
    };
  });
}

function addMaterial() {
  setForm((prev) => {
    if (!prev) return null;

    return {
      ...prev,
      materials: [...(prev.materials || []), { id: Date.now(), name: "", quantity: 0 }],
    };
  });
}


function removeMaterial(index: number) {
  setForm((prev) => {
    if (!prev) return null;

    const updated = [...(prev.materials || [])];
    updated.splice(index, 1);

    return {
      ...prev,
      materials: updated,
    };
  });
}




  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form) onSaveLocal(form);
  }


  const tierStyles = {
    T1: {
      modal:
        "rounded-2xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border border-blue-800 shadow-2xl text-white",

      label: "text-[#a0c4ff] mb-1",
      input:
        "bg-slate-800 border border-blue-800 text-white focus:ring-blue-400 focus:border-blue-400",
        
      dropdown:
        " border border-blue-800 text-blue-100 shadow-lg rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500",

      dropdownItem:
        "px-4 py-2 rounded-md text-blue-100 hover:bg-blue-800 hover:text-blue-200 focus:bg-blue-900 focus:text-white cursor-pointer transition-colors",
      
      selectValue: "bg-slate-800 border border-blue-800 text-white focus:ring-blue-400 focus:border-blue-400",
      
      selectTrigger:
        "bg-slate-800 border border-blue-800 text-white focus:ring-blue-400 focus:border-blue-400",

      selectContent: "bg-slate-900 text-white",


      buttonPrimary:
        "bg-blue-700 hover:bg-blue-500 focus:ring-blue-500 text-white",
      buttonSecondary:
        "bg-slate-900 text-blue-300 hover:bg-blue-700",
      title: "text-blue-300",
    },

    T2: {
      modal:
        "rounded-2xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-yellow-900 via-amber-900 to-orange-950 border border-amber-700 shadow-2xl text-[#f0e4c1]",

      label: "text-[#f9d58b] mb-1",
      input:
        "bg-[#5c3b0d] border border-amber-700 text-[#f0e4c1] focus:ring-amber-400 focus:border-amber-400",

      dropdown:
        "bg-[#4a2e08] via-amber-900 to-orange-950 border border-amber-700 text-[#f0e4c1] shadow-lg rounded-xl focus:ring-2 px-3 focus:ring-amber-400 focus:border-amber-400",

      dropdownItem:
        "px-4 py-2 rounded-md text-amber-100 hover:bg-amber-900 hover:text-amber-200 focus:bg-amber-950 focus:text-white cursor-pointer transition-colors",

      selectTrigger:
        "bg-[#5c3b0d] border border-amber-700 text-amber-100 focus:ring-amber-400 focus:border-amber-400 [&>[data-placeholder]]:text-amber-400",
      
      selectValue: "bg-[#5c3b0d] border border-amber-700 text-amber-100 focus:ring-amber-400 focus:border-amber-400",
      
      selectContent: "bg-[#3e2f0f] text-[#f0e4c1]",

      buttonPrimary:
        "bg-amber-700 hover:bg-amber-500 focus:ring-amber-500 text-[#0c0802]",
      buttonSecondary:
        "bg-[#3b2e08] text-amber-500 hover:bg-amber-900",
      title: "text-amber-400",
    },
  };


 const styles = tierStyles[form.tier || "T1"]; // fallback to T1 if tier missing

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className={`max-w-lg rounded-lg shadow-lg overflow-hidden ${styles.modal}`}
      >
        <DialogHeader>
          <DialogTitle className={`text-2xl font-semibold ${styles.title}`}>
            Edit Blueprint
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 overflow-x-hidden">
          <Input type="hidden" name="id" value={form.id} />

          <div>
            <Label htmlFor="editBlueprintName" className={styles.label}>
              Blueprint Name
            </Label>
            <Input
              id="editBlueprintName"
              name="name"
              value={form.name}
              onChange={handleChange}
              required
              className={`${styles.input} w-full`}
            />
          </div>

          <div>
            <Label htmlFor="editBlueprintSellPrice" className={styles.label}>
              Sell Price
            </Label>
            <Input
              id="editBlueprintSellPrice"
              name="sell_price"
              type="number"
              step="0.01"
              value={form.sell_price}
              onChange={handleChange}
              required
              className={`${styles.input} w-full`}
            />
          </div>

          <div>
            <Label htmlFor="editBlueprintCost" className={styles.label}>
              Material Cost
            </Label>
            <Input
              id="editBlueprintCost"
              name="material_cost"
              type="number"
              step="0.01"
              value={form.material_cost}
              onChange={handleChange}
              required
              className={`${styles.input} w-full`}
            />
          </div>

          <div>
            <Label htmlFor="editBlueprintStation" className={styles.label}>
              Manufacturing Station
            </Label>
            <select
              id="editBlueprintStation"
              name="station_id"
              value={form.station_id || ""}
              onChange={handleChange}
              className={`${styles.input} w-full rounded-md py-2 px-1.5`}
            >
              <option value="">None (Use Jita)</option>
              {stations.map((station) => (
                <option key={station.station_id} value={station.station_id}>
                  {station.name} ({station.station_id})
                </option>
              ))}
            </select>
          </div>
         <div>
           <Label htmlFor="blueprintParseAmtPerRun" className={`${styles.label} mb-1 block`}>
             Amount per Run
           </Label>
           <div className="flex items-center gap-3">
             <Select
               value={isCustom ? "custom" : String(amtPerRun ?? 1)}
               onValueChange={(value) => {
                 if (value === "custom") {
                   setIsCustom(true);
                 } else {
                   const numeric = Number(value);
                   setIsCustom(false);
                   setAmtPerRun(numeric);
                   setForm((prev) =>
                     prev ? { ...prev, amt_per_run: numeric } : prev
                   );
                 }
               }}
             >
               <SelectTrigger
                 id="blueprintParseAmtPerRun"
                 className={`${styles.selectTrigger} ${styles.dropdown} h-10 pl-4 mt-2 scale-110 mx-2 custom-select-trigger`}
               >
                 <SelectValue />
                
               </SelectTrigger>
               <SelectContent className={styles.selectContent}>
                 <SelectItem value="100">100 Units</SelectItem>
                 <SelectItem value="1">1 Unit</SelectItem>
                 <SelectItem value="custom">Custom…</SelectItem>
               </SelectContent>
             </Select>
             {isCustom && (
               <input
               type="number"
               min={1}
               value={customAmtPerRun}
               onChange={(e) => {
                 const val = Number(e.target.value);
                 setCustomAmtPerRun(val);
                 setForm((prev) =>
                   prev ? { ...prev, amt_per_run: val } : prev
                 );
               }}
               className={`${styles.input} w-full rounded-md py-2 px-1.5`}
               />
             )}
           </div>
         </div>

          <div>
            <Label htmlFor="editBlueprintTier" className={styles.label}>
              Tier
            </Label>
            <Select value={form.tier} onValueChange={handleTierChange}>
              <SelectTrigger
                id="editBlueprintTier"
                className={`${styles.selectTrigger} max-w-50 scale-110 mx-2`}
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className={styles.selectContent}>
                <SelectItem value="T1">Tier 1</SelectItem>
                <SelectItem value="T2">Tier 2</SelectItem>
              </SelectContent>
            </Select>

            
          </div>

          

          {form.tier === "T2" && (
            <>
              <div>
                <Label
                  htmlFor="editBlueprintInventionChance"
                  className={styles.label}
                >
                  Invention Chance (%)
                </Label>
                <Input
                  id="editBlueprintInventionChance"
                  name="invention_chance"
                  type="number"
                  min={0}
                  max={100}
                  step={0.1}
                  value={form.invention_chance ? form.invention_chance * 100 : ""}
                  onChange={handleInventionChanceChange}
                  className={`${styles.input} max-w-25`}
                />
              </div>

              <div>
                <Label
                  htmlFor="editBlueprintRunsPerCopy"
                  className={styles.label}
                >
                  Runs per Invented Copy
                </Label>
                <Select
                  value={String(form.runs_per_copy || 10)}
                  onValueChange={handleRunsPerCopyChange}
                >
                  <SelectTrigger
                    id="editBlueprintRunsPerCopy"
                    className={`${styles.selectTrigger} max-w-50`}
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className={styles.selectContent}>
                    <SelectItem value="10">10 Runs</SelectItem>
                    <SelectItem value="1">1 Run</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          <div className="mt-4">
            <h3 className="text-lg font-semibold mb-2">Materials</h3>
            {(form.materials || []).map((material: Material, idx: number) => (
              <div key={material.id ?? idx} className="flex gap-2 items-center mb-2">
                <Input
                  type="text"
                  placeholder="Name"
                  value={material.name}
                  onChange={(e) => updateMaterialField(idx, "name", e.target.value)}
                  className="w-1/3"
                />
                <Input
                  type="number"
                  placeholder="Qty"
                  value={material.quantity}
                  min={0}
                  onChange={(e) => updateMaterialField(idx, "quantity", parseInt(e.target.value) || 0)}
                  className="w-1/4"
                />
                {(() => {
                  const isOther = material.category === "Other";
                  const isCustom =
                    material.category &&
                    !["Minerals", "Items", "Components", "Invention Materials", "Reaction Materials", "Planetary Materials", "Other"].includes(material.category);

                  return (
                    <>
                      <Select
                        value={isCustom ? "Other" : material.category || ""}
                        onValueChange={(val) => {
                          if (val === "Other") {
                            updateMaterialField(idx, "category", "Other");
                          } else {
                            updateMaterialField(idx, "category", val);
                          }
                        }}
                      >
                        <SelectTrigger className={styles.selectTrigger}>
                          <SelectValue placeholder="Select category" className={styles.selectValue} />
                        </SelectTrigger>
                        <SelectContent className={styles.selectContent}>
                          <SelectItem value="Minerals" className={styles.dropdownItem}>Minerals</SelectItem>
                          <SelectItem value="Items">Items</SelectItem>
                          <SelectItem value="Components">Components</SelectItem>
                          <SelectItem value="Invention Materials">Invention Materials</SelectItem>
                          <SelectItem value="Reaction Materials">Reaction Materials</SelectItem>
                          <SelectItem value="Planetary Materials">Planetary Materials</SelectItem>
                          <SelectItem value="Other" className={styles.dropdownItem}>Other</SelectItem>
                        </SelectContent>
                      </Select>

                      {(isOther || isCustom) && (
                        <Input
                          type="text"
                          placeholder="Enter custom category"
                          value={material.category || ""}
                          onChange={(e) => updateMaterialField(idx, "category", e.target.value)}
                          className={styles.selectTrigger}
                        />
                      )}
                    </>
                  );
                })()}


                <Button
                  type="button"
                  variant="destructive"
                  onClick={() => removeMaterial(idx)}
                  className="w-1/6"
                >
                  Remove
                </Button>
              </div>
            ))}
            <Button type="button" onClick={addMaterial} variant="secondary" className="mt-2">
              + Add Material
            </Button>
          </div>

          <DialogFooter>
            <Button type="submit" className={styles.buttonPrimary}>
              Save Changes
            </Button>
            <DialogClose asChild>
              <Button type="button" variant="secondary" className={styles.buttonSecondary}>
                Cancel
              </Button>
            </DialogClose>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
