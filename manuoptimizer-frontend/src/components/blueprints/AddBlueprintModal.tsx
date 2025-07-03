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
import { useMemo, useState } from "react";
import { E } from "vitest/dist/chunks/environment.d.cL3nLXbE.js";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { ScrollArea } from "../ui/scroll-area";
import { DropdownMenu } from "@radix-ui/react-dropdown-menu";
import { DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "../ui/dropdown-menu";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { cn } from "@/lib/utils";

interface AddBlueprintModalProps {
  open: boolean
  onSubmit: (data: {
    blueprintPaste: string;
    sell_price: number;
    amt_per_run: number;
    material_cost: number;
    tier: "T1" | "T2";
    invention_materials?: string;
    invention_chance?: number;
    runs_per_copy?: number;
  }) => Promise<void>
  onClose: () => void
  onBlueprintAdded?: () => void
}


const tierStyles = {
  T1: {
    modal:
      "rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border border-blue-800 shadow-2xl text-white",

    label: "text-blue-300",

    input:
      "bg-slate-800 border border-blue-700 text-blue-100 placeholder:text-blue-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500",

    li:
      "text-blue-100",

    dropdown:
      " border border-blue-800 text-blue-100 shadow-lg rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
    
    dropdownItem:
      "px-4 py-2 rounded-md text-blue-100 hover:bg-blue-800 hover:text-blue-200 focus:bg-blue-900 focus:text-white cursor-pointer transition-colors",

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
    
    li:
      "text-amber-100",
    
    dropdown:
      "bg-[#4a2e08] via-amber-900 to-orange-950 border border-amber-700 text-[#f0e4c1] shadow-lg rounded-xl focus:ring-2 px-3 focus:ring-amber-400 focus:border-amber-400",
    
    dropdownItem:
      "px-4 py-2 rounded-md text-amber-100 hover:bg-amber-900 hover:text-amber-200 focus:bg-amber-950 focus:text-white cursor-pointer transition-colors",

    selectTrigger:
      "bg-[#4a2e08] border border-amber-600 text-[#f0e4c1] focus:ring-2 focus:ring-amber-400 focus:border-amber-400",

    selectContent: "bg-[#3e2f0f] text-[#f0e4c1]",

    buttonPrimary:
      "bg-amber-700 hover:bg-amber-600 focus:ring-2 focus:ring-amber-500 text-black font-semibold",

    buttonSecondary:
      "bg-[#2e1e06] text-amber-300 hover:bg-amber-800 hover:text-white border border-amber-600",

    title: "text-amber-400",

    description: "text-amber-400",
  },
};

export default function AddBlueprintModal({ 
  open,
  onClose,
  onBlueprintAdded 
}: AddBlueprintModalProps) {
  const [tier, setTier] = useState<"T1" | "T2">("T1");
  const [mode, setMode] = useState<"game" | "isk">("game");
  const [blueprintData, setBlueprintData] = useState("");
  const [inventionData, setInventionData] = useState("");
  const [inventionChance, setInventionChance] = useState("");
  const runsPerCopyOptions = [1, 10];
  const [runsPerCopy, setRunsPerCopy] = useState(runsPerCopyOptions[1]);
  const [sellPrice, setSellPrice] = useState("");
  const [makeCost, setMakeCost] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const styles = tierStyles[tier];
  const [isCustom, setIsCustom] = useState(false);
  const [amtPerRun, setAmtPerRun] = useState<number>(1);
  const [customAmtPerRun, setCustomAmtPerRun] = useState<number | undefined>(undefined);

  const showInvention = tier === "T2" && mode === "game";

  const parsedMaterials = useMemo(() => {
    const lines = blueprintData.trim().split("\n");
    const inventionLines = inventionData.trim().split("\n");

    const preview: Record<string, { name: string; quantity: number; unitPrice?: number }[]> = {};
    let blueprintName = "";
    let blueprintTypeId = "";
    let isFirstLine = true;

    function parseLines(lines: string[], isInvention = false) {
      let localCategory = isInvention ? "Invention Materials / Uncategorized" : "Uncategorized";
      let localParsingTable = false;

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        if (isFirstLine && !isInvention) {
          const [name, typeId] = line.split("\t");
          blueprintName = name?.replace("Blueprint", "").trim();
          blueprintTypeId = typeId?.trim();
          isFirstLine = false;
          continue;
        }

        if (/^(Items|Minerals|Components|Planetary materials|Datacores|Optional items)$/i.test(line)) {
          localCategory = isInvention
            ? `Invention Materials / ${line}`
            : line;
          if (line === "Optional items" && isInvention && lines[i + 2]?.startsWith("No item selected")) {
            i += 2;
            continue;
          }
          preview[localCategory] = [];
          localParsingTable = false;
          continue;
        }

        if (/^Item\tRequired\tAvailable\tEst\..*price\ttypeID$/i.test(line)) {
          localParsingTable = true;
          continue;
        }

        if (!localParsingTable) continue;

        const [name, requiredStr, _available, unitPriceStr] = line.split("\t");
        const required = parseInt(requiredStr);
        const unitPrice = parseFloat(unitPriceStr);

        if (name && !isNaN(required)) {
          // Adjust unit price for invention materials to reflect invention chance
          const adjustedUnitPrice = isInvention && inventionChance
            ? (isNaN(unitPrice) ? undefined : unitPrice / (parseFloat(inventionChance) > 1 ? parseFloat(inventionChance) / 100 : parseFloat(inventionChance)))
            : (isNaN(unitPrice) ? undefined : unitPrice);

          preview[localCategory] ??= [];
          preview[localCategory].push({
            name: name.trim(),
            quantity: required,
            unitPrice: adjustedUnitPrice,
          });
        }
      }
    }

    parseLines(lines);
    if (showInvention) parseLines(inventionLines, true);

    const orderedPreview: typeof preview = {};

    if (blueprintName && blueprintTypeId) {
      orderedPreview["Blueprint Info"] = [
        { name: `Name: ${blueprintName}`, quantity: 0 },
        { name: `Type ID: ${blueprintTypeId}`, quantity: 0 },
      ];
    }

    if (inventionChance && showInvention) {
      orderedPreview["Invention Metadata"] = [
        { name: `Invention Chance: ${inventionChance}%`, quantity: 0 },
      ];
    }

    // Append rest
    for (const [k, v] of Object.entries(preview)) {
      if (!(k in orderedPreview)) orderedPreview[k] = v;
    }

    return orderedPreview;
  }, [blueprintData, inventionData, inventionChance, showInvention]);





  async function handleSubmit(e: { preventDefault: () => void; }) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const res = await fetch("/api/blueprints/blueprints", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          blueprint_paste: blueprintData,
          invention_materials: inventionData,
          sell_price: parseFloat(sellPrice) || 0,
          amt_per_run: amtPerRun || 1,
          material_cost: parseFloat(makeCost) || 0,
          tier,
          invention_chance: inventionChance ? parseFloat(inventionChance) : null,
          runs_per_copy: tier === "T2" ? runsPerCopy : null
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Unknown error");
      }
      setSuccess(true);
      setTimeout(() => onClose(), 1500);
    } catch (err: any) {
      console.error("Error adding blueprint:", err);
      setError(err.message || "Failed to add blueprint");
    } finally {
      onBlueprintAdded?.();
      console.log("Added blueprint data:", blueprintData);
      setLoading(false);
    }
  }



  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
    <div className="w-full overflow-x-hidden">
      <DialogContent
        className={cn(
          tierStyles[tier].modal,
          "max-w-2xl w-full max-h-[90vh] overflow-y-auto px-4" // Add padding instead of scale
        )}
      >
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
                className={`${styles.input} placeholder:${styles.label} min-h-[120px] resize-y w-full break-words`}
                style={{ wordBreak: "break-word" }}
              />

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
                       setIsCustom(false);
                       setAmtPerRun(Number(value));
                     }
                   }}
                 >
                   <SelectTrigger
                     id="blueprintParseAmtPerRun"
                     className={`${styles.selectTrigger} ${styles.dropdown} h-10 pl-4 mt-2 scale-110 mx-2 custom-select-trigger`}
                   >
                     <SelectValue placeholder="Choose amount..." />
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
                     onChange={(e) => setCustomAmtPerRun(Number(e.target.value))}
                     className="w-32 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-700 text-blue-100 text-sm mt-2 h-10"
                     placeholder="Custom amount"
                   />
                 )}
               </div>
             </div>

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
                    onChange={(e) => {
                      const value = e.target.value;
                      if (value === "" || !isNaN(parseFloat(value))) {
                        setInventionChance(value);
                      }
                    }}
                    className={`${styles.input} placeholder:${styles.label}`}
                  />
                  <div>
                    <label
                      htmlFor="blueprintParseRunsPerCopy"
                      className={styles.label}
                    >
                      Runs per Invented Copy
                    </label>
                    <div className="mt-2" />
                    <select
                      id="blueprintParseRunsPerCopy"
                      name="blueprintParseRunsPerCopy"
                      value={runsPerCopy}
                      onChange={e => setRunsPerCopy(Number(e.target.value))}
                      className={`${styles.selectTrigger} ${styles.dropdown} h-10 pl-4`}
                    >
                      <option className={styles.dropdownItem} value={10} selected>10 Runs</option>
                      <option className={styles.dropdownItem} value={1}>1 Run</option>
                    </select>
                  </div>

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

          {Object.keys(parsedMaterials).length > 0 && (
            <div className={`${styles.input} rounded-lg p-4 text-sm`}>
              <strong className={`block mb-2 ${styles.title}`}>Parsed Preview:</strong>
              <ScrollArea className="h-80 pr-2 px-2 scroll-py-2.5 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
              <div className="w-full space-y-4 break-words">
                {Object.entries(parsedMaterials).map(([category, items]) => (
                  <div key={category} className="mb-4">
                    <div className={`${styles.title} font-semibold mb-1`}>{category}</div>
                    <ul className={`${styles.label} space-y-1`}>
                      {items.map(({ name, quantity, unitPrice }) => (
                        <li key={name} className={`${styles.li} flex justify-between`}>
                          {category === "Blueprint Info" || category === "Invention Metadata" ? (
                            <span className={styles.li}>{name}</span>
                          ) : (
                            <>
                              <span className={styles.li}>{name}</span>
                              <span className={styles.li}>
                                {quantity} {unitPrice !== undefined ? `× ${unitPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })} ISK` : ""}
                              </span>
                            </>
                          )}
                        </li>
                      ))}
                      {category !== "Blueprint Info" && category !== "Invention Metadata" && (
                        <li className="flex justify-between">
                          <span className={styles.description}>Total:</span>
                          <span className={styles.label}>
                            {items.reduce((acc, { quantity, unitPrice }) => acc + (quantity * (unitPrice ?? 0)), 0).toLocaleString(undefined, { maximumFractionDigits: 2 })} ISK
                          </span>
                        </li>
                      )}
                    </ul>
                  </div>
                ))}
                <div className="mt-4">
                  <strong className={`block mb-2 ${styles.title}`}>Est. Price:</strong>
                  <span className={styles.label}>
                    {Object.values(parsedMaterials).reduce((acc, items) => acc + items.reduce((acc, { quantity, unitPrice }) => acc + (quantity * (unitPrice ?? 0)), 0), 0).toLocaleString(undefined, { maximumFractionDigits: 2 })} ISK
                  </span>
                </div>
              </div>
              </ScrollArea>
            </div>
          )}



          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <AlertTriangle className="w-4 h-4" />
              {error}
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 text-green-400 text-sm">
              <CheckCircle2 className="w-4 h-4" />
              Blueprint added successfully!
            </div>
          )}


          <div className="grid grid-cols-2 gap-4">
            <Input
              placeholder="Sell Price (Leave as 0 for auto)"
              value={sellPrice}
              onChange={(e) => setSellPrice(e.target.value)}
              className={`${styles.input} placeholder:${styles.label}`}
            />
            <Input
              placeholder="Make Cost (Leave as 0 for auto)"
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
      </div>
    </Dialog>
  );
}
