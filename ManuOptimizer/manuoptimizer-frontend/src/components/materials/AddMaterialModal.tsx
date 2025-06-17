import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { RadioGroup, RadioGroupItem } from "../ui/radio-group";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";

interface AddMaterialModalProps {
    open: boolean;
    onClose: () => void;
    onSubmit: (data: {
        materialsText: string;updateType: "replace" | "add"
    }) => Promise < void > ;
}
export function AddMaterialModal({
    open,
    onClose,
    onSubmit
}: AddMaterialModalProps) {
    const [materialsText, setMaterialsText] = useState("");
    const [updateType, setUpdateType] = useState < "replace" | "add" > ("replace");
    const [loading, setLoading] = useState(false);
    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!materialsText.trim()) return;
        setLoading(true);
        try {
            await onSubmit({
                materialsText,
                updateType
            });
            setMaterialsText("");
            setUpdateType("replace");
            onClose();
        } catch (err) {
            console.error("Error submitting materials:", err);
            alert("Error submitting materials, see console.");
        } finally {
            setLoading(false);
        }
    }
    return (<Dialog open={open} onOpenChange={(open) => !open && onClose()}>
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
            value={updateType}
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

          <div className="flex justify-end space-x-2 pt-2">
            <Button type="submit" className="bg-blue-700 hover:bg-blue-800 text-white" disabled={loading}>
              {loading ? "Updating..." : "Update Available Materials"}
            </Button>
            <Button type="button" variant="secondary" className="bg-slate-700 text-blue-200 hover:bg-slate-600" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>);
}