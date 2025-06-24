import React, { useState, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { RadioGroup, RadioGroupItem } from "../ui/radio-group";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { ScrollArea } from "../ui/scroll-area";
import { CheckCircle2, AlertTriangle } from "lucide-react";

interface AddMaterialModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { materialsText: string; updateType: "replace" | "add"; }) => Promise<void>
}

export function AddMaterialModal({ open, onClose }: AddMaterialModalProps) {
  const [materialsText, setMaterialsText] = useState("");
  const [updateType, setUpdateType] = useState<"replace" | "add">("replace");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const parsedMaterials = useMemo(() => {
    const lines = materialsText.trim().split("\n");
    return lines
      .map((line) => {
        const [name, qtyStr] = line.split("\t");
        const quantity = parseInt(qtyStr);
        return name && !isNaN(quantity)
          ? { name: name.trim(), quantity }
          : null;
      })
      .filter((item): item is { name: string; quantity: number } => item !== null);
  }, [materialsText]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    if (!parsedMaterials.length) return;

    const materials: Record<string, number> = {};
    parsedMaterials.forEach(({ name, quantity }) => {
      materials[name] = quantity;
    });

    setLoading(true);
    try {
      const res = await fetch("/materials/update_materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ materials, updateType }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Unknown error");
      }

      setMaterialsText("");
      setUpdateType("replace");
      setSuccess(true);
      setTimeout(() => onClose(), 1500);
    } catch (err: any) {
      console.error("Error submitting materials:", err);
      setError(err.message || "Failed to submit materials");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-2xl w-full max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-blue-300 text-lg font-semibold">
            Add Available Materials From Game (Copy/Paste)
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Textarea
            placeholder="Paste available materials here"
            required
            value={materialsText}
            onChange={(e) => setMaterialsText(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-blue-100 placeholder:text-blue-400 resize-y min-h-[120px]"
          />

          <RadioGroup
            defaultValue="add"
            onValueChange={(val) => setUpdateType(val as "replace" | "add")}
            className="flex flex-col gap-4 text-blue-200"
          >
            <Label htmlFor="addToMaterials" className="flex items-center gap-2 cursor-pointer select-none">
              <RadioGroupItem
                id="addToMaterials"
                value="add"
                className="border-blue-500 data-[state=checked]:bg-blue-400 data-[state=checked]:border-blue-200"
              />
              Add to existing materials (Replaces materials with the same name)
            </Label>

            <Label htmlFor="replaceMaterials" className="flex items-center gap-2 cursor-pointer select-none">
              <RadioGroupItem
                id="replaceMaterials"
                value="replace"
                className="border-blue-500 data-[state=checked]:bg-blue-400 data-[state=checked]:border-blue-200"
              />
              Replace ALL materials (Deletes all existing materials)
            </Label>
          </RadioGroup>

          {parsedMaterials.length > 0 && (
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-sm text-blue-200">
              <strong className="block mb-2 text-blue-400">Parsed Preview:</strong>
              <ScrollArea className="h-40 pr-2">
                <ul className="space-y-1">
                  {parsedMaterials.map(({ name, quantity }) => (
                    <li key={name} className="flex justify-between">
                      <span>{name}</span>
                      <span className="text-blue-300">{quantity}</span>
                    </li>
                  ))}
                </ul>
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
              Materials updated successfully!
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-2">
            <Button
              type="submit"
              className="bg-blue-700 hover:bg-blue-800 text-white"
              disabled={loading || !parsedMaterials.length}
            >
              {loading ? "Updating..." : "Update Available Materials"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="bg-slate-700 text-blue-200 hover:bg-slate-600"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
