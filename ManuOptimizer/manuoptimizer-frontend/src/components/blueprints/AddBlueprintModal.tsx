// Truncated for brevity, assumes `AddBlueprintModal` file continues below.
// Here's how to fix and finalize your integration:

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "../ui/dialog";
import { Textarea } from "../ui/textarea";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Label } from "../ui/label";
import { RadioGroup, RadioGroupItem } from "../ui/radio-group";
import { toast } from "react-hot-toast";
import { useState } from "react";

interface AddBlueprintModalProps {
  open: boolean
  onSubmit: (data: {
    materials: string;
    sell_price: number;
    material_cost: number;
    tier: "T1" | "T2";
    invention_materials?: string;
    invention_chance?: number;
    runs_per_copy?: number;
  }) => Promise<void>
  onClose: () => void
}


const tierStyles = {
  T1: {
    modal:
      "rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border border-blue-800 shadow-2xl text-white",

    label: "text-blue-300",

    input:
      "bg-slate-800 border border-blue-700 text-blue-100 placeholder:text-blue-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500",

    selectTrigger:
      "bg-slate-800 border border-blue-700 text-blue-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500",

    selectContent: "bg-slate-900 text-white",

    buttonPrimary:
      "bg-blue-600 hover:bg-blue-500 focus:ring-2 focus:ring-blue-400 text-white font-semibold",

    buttonSecondary:
      "bg-slate-800 text-blue-300 hover:bg-blue-800 hover:text-white border border-blue-700",

    title: "text-blue-300",

    description: "text-blue-400",
  },

  T2: {
    modal:
      "rounded-2xl bg-gradient-to-br from-yellow-950 via-amber-900 to-orange-950 border border-amber-700 shadow-2xl text-[#f0e4c1]",

    label: "text-amber-300",

    input:
      "bg-[#4a2e08] border border-amber-600 text-[#f0e4c1] placeholder:text-amber-300 focus:ring-2 focus:ring-amber-400 focus:border-amber-400 ",

    selectTrigger:
      "bg-[#4a2e08] border border-amber-600 text-[#f0e4c1] focus:ring-2 focus:ring-amber-400 focus:border-amber-400",

    selectContent: "bg-[#3e2f0f] text-[#f0e4c1]",

    buttonPrimary:
      "bg-amber-700 hover:bg-amber-600 focus:ring-2 focus:ring-amber-500 text-black font-semibold",

    buttonSecondary:
      "bg-[#2e1e06] text-amber-300 hover:bg-amber-800 hover:text-white border border-amber-600",

    title: "text-amber-400",

    description: "text-amber-300",
  },
};

export default function AddBlueprintModal({ open, onClose }: AddBlueprintModalProps) {
  const [tier, setTier] = useState<"T1" | "T2">("T1");
  const [mode, setMode] = useState<"game" | "isk">("game");
  const [blueprintData, setBlueprintData] = useState("");
  const [inventionData, setInventionData] = useState("");
  const [inventionChance, setInventionChance] = useState("");
  const [sellPrice, setSellPrice] = useState("");
  const [makeCost, setMakeCost] = useState("");
  const [loading, setLoading] = useState(false);
  const styles = tierStyles[tier];

  const showInvention = tier === "T2";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    const url = mode === "isk" ? "/api/blueprints/blueprint" : "/api/blueprints/from-game";
    const body =
      mode === "isk"
        ? {
            name: extractBlueprintName(blueprintData),
            materials: blueprintData,
            sell_price: parseFloat(sellPrice),
            material_cost: parseFloat(makeCost),
          }
        : {
            blueprintData,
            inventionData,
            inventionChance,
            sellPrice,
            makeCost,
            tier,
          };

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error("Failed to add blueprint");

      toast.success("Blueprint added successfully");
      onClose();
    } catch (error) {
      toast.error("Failed to add blueprint");
      console.error("Error adding blueprint:", error);
    } finally {
      setLoading(false);
    }
  }

  function extractBlueprintName(raw: string): string {
    const lines = raw.split("\n");
    const match = lines[0]?.match(/['"]?([^'"]+) Blueprint['"]?/i);
    return match ? match[1] : "Unknown Blueprint";
  }

  


  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className={tierStyles[tier].modal + " w-full max-w-2xl scale-110"}>
        <DialogHeader className="mb-4">
          <DialogTitle className={tierStyles[tier].title + " text-lg font-semibold"}>
            Add Blueprint
          </DialogTitle>
          <DialogDescription className={styles.description}>
            Paste in your blueprint data from game or ISK/hour
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className={styles.label + " flex gap-4"}>
            <Label className="flex items-center gap-2">
              <input type="radio" checked={mode === "game"} onChange={() => setMode("game")} /> From Game
            </Label>
            <Label className={tierStyles[tier].label}>
              <input type="radio" checked={mode === "isk"} onChange={() => setMode("isk")} /> From ISK/Hour
            </Label>
          </div>

          {mode === "game" && (
            <>
              <RadioGroup
                value={tier}
                onValueChange={(val) => setTier(val as "T1" | "T2")}
                className={`flex gap-4 ${styles.label}`}
              >
                <Label htmlFor="T1" className="flex items-center gap-2 cursor-pointer select-none">
                  <RadioGroupItem
                    id="T1"
                    value="T1"
                    className="border-blue-500 data-[state=checked]:bg-blue-400 data-[state=checked]:ring-2 data-[state=checked]:ring-blue-500"
                  />
                  T1
                </Label>
                <Label htmlFor="T2" className="flex items-center gap-2 cursor-pointer select-none">
                  <RadioGroupItem
                    id="T2"
                    value="T2"
                    className="border-amber-500 data-[state=checked]:bg-amber-400 data-[state=checked]:ring-2 data-[state=checked]:ring-amber-500"
                  />
                  T2
                </Label>
              </RadioGroup>


              <Textarea
                placeholder="Paste blueprint data from game"
                value={blueprintData}
                onChange={(e) => setBlueprintData(e.target.value)}
                className={`${styles.input} placeholder:${styles.label} min-h-[120px] resize-y `}
              />

              {showInvention && (
                <>
                  <Textarea
                    placeholder="Paste invention materials"
                    value={inventionData}
                    onChange={(e) => setInventionData(e.target.value)}
                    className={`${styles.input} placeholder:${styles.label}`}
                  />
                  <Input
                    placeholder="Invention chance % (e.g. 42.5)"
                    value={inventionChance}
                    onChange={(e) => setInventionChance(e.target.value)}
                    className={`${styles.input} placeholder:${styles.label}`}
                  />
                </>
              )}
            </>
          )}

          {mode === "isk" && (
            <Textarea
              placeholder="Paste ISK/hour format material list here"
              value={blueprintData}
              onChange={(e) => setBlueprintData(e.target.value)}
              className={`${styles.input} placeholder:${styles.label} min-h-[120px] resize-y`}
            />
          )}

          <div className="grid grid-cols-2 gap-4">
            <Input
              placeholder="Sell Price"
              value={sellPrice}
              onChange={(e) => setSellPrice(e.target.value)}
              className={`${styles.input} placeholder:${styles.label}`}
            />
            <Input
              placeholder="Make Cost"
              value={makeCost}
              onChange={(e) => setMakeCost(e.target.value)}
              className={`${styles.input} placeholder:${styles.label}`}
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button
              type="submit"
              className={tierStyles[tier].buttonPrimary}
              disabled={loading}
            >
              {loading ? "Adding..." : "Add Blueprint"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              className={tierStyles[tier].buttonSecondary}
              onClick={onClose}
            >
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
