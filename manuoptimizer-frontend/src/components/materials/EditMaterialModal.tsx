'use client';
import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Material } from "@/types/materials";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

interface EditMaterialModalProps {
    material: Material | null;
    open: boolean;
    onClose: () => void;
    onSave: (updated: Material) => void;
}
export function EditMaterialModal({
    material,
    open,
    onClose,
    onSave
}: EditMaterialModalProps) {
    const [quantity, setQuantity] = useState(0);
    const [typeId, setTypeId] = useState < number | undefined > ();
    const [category, setCategory] = useState("Other");
    const [manualCategory, setManualCategory] = useState("");
    useEffect(() => {
        if (material) {
            setQuantity(material.quantity);
            setTypeId(material.type_id ?? undefined);
            setCategory(material.category || "Other");
            setManualCategory("");
        }
    }, [material]);
    async function handleSubmit(e: React.FormEvent) {
      e.preventDefault();
      if (!material) return;

      const updatedMaterial: Material = {
        ...material,
        quantity,
        type_id: typeId,
        category: category === "Other" ? manualCategory : category,
      };

      onSave(updatedMaterial); // Let parent handle PUT + fetch
    }
    return (<Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-2xl w-full">
        <DialogHeader>
          <DialogTitle className="text-blue-300">
            Edit Material{material ? `: ${material.name}` : ""}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="number"
            placeholder="Quantity"
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            required
            className="bg-slate-900 border border-slate-700 text-blue-100"
          />
          <Input
            type="number"
            placeholder="Type ID (optional)"
            value={typeId ?? ""}
            onChange={(e) => setTypeId(Number(e.target.value))}
            className="bg-slate-900 border border-slate-700 text-blue-100"
          />
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="bg-slate-900 border border-slate-700 text-blue-100">
              <SelectValue placeholder="Select category" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 text-blue-100">
              <SelectItem value="Minerals">Minerals</SelectItem>
              <SelectItem value="Items">Items</SelectItem>
              <SelectItem value="Components">Components</SelectItem>
              <SelectItem value="Invention Materials">Invention Materials</SelectItem>
              <SelectItem value="Reaction Materials">Reaction Materials</SelectItem>
              <SelectItem value="Planetary Materials">Planetary Materials</SelectItem>
              <SelectItem value="Other">Other</SelectItem>
            </SelectContent>
          </Select>
          {category === "Other" && (
            <Input
              type="text"
              placeholder="Enter custom category"
              value={manualCategory}
              onChange={(e) => setManualCategory(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-blue-100"
            />
          )}
          <div className="flex justify-end space-x-2 pt-4">
            <Button type="submit" className="bg-blue-700 hover:bg-blue-800 text-white">
              Save
            </Button>
            <Button type="button" variant="secondary" className="bg-slate-700 text-blue-200" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>);
}