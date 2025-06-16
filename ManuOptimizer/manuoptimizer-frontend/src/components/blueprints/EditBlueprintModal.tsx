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
import { useState } from "react";
import { BlueprintTier } from "@/types/blueprints";

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


  React.useEffect(() => {
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
    if (value === "T2") {
      return {
        ...prev,
        tier: "T2",
        invention_chance: (prev as any).invention_chance ?? 0,
        invention_cost: (prev as any).invention_cost ?? 0,
        full_material_cost: (prev as any).full_material_cost ?? prev.material_cost ?? 0,
        runs_per_copy: (prev as any).runs_per_copy ?? 10,
      } as BlueprintT2;
    } else {
      // Use type assertion here to tell TypeScript these properties might exist
      const { invention_chance, invention_cost, full_material_cost, runs_per_copy, ...rest } = 
        prev as (BlueprintBase & { 
          invention_chance?: number; 
          invention_cost?: number; 
          full_material_cost?: number; 
          runs_per_copy?: number 
        });
      return {
        ...rest,
        tier: "T1",
      } as BlueprintT1;
    }
  });
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

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form) onSave(form);
  }


  const tierStyles = {
  T1: {
    modal: "bg-[#0a1b38] border border-[#1a3a8a] text-white",
    label: "text-[#a0c4ff]",
    input:
      "bg-[#142850] border border-[#2a4d8f] text-white focus:ring-[#6bb0ff] focus:border-[#6bb0ff]",
    selectTrigger:
      "bg-[#142850] border border-[#2a4d8f] text-white focus:ring-[#6bb0ff] focus:border-[#6bb0ff]",
    selectContent: "bg-[#0a1f44] text-white",
    buttonPrimary:
      "bg-[#1e40af] hover:bg-[#3b82f6] focus:ring-[#3b82f6] text-white",
    buttonSecondary:
      "bg-[#0f172a] text-[#6bb0ff] hover:bg-[#1e40af]",
    title: "text-[#6bb0ff]",
  },
  T2: {
    modal: "bg-[#42210b] border border-[#8a5e1a] text-[#f0e4c1]",
    label: "text-[#d9bb7f]",
    input:
      "bg-[#6a4b1b] border border-[#9e7c31] text-[#f0e4c1] focus:ring-[#d4af37] focus:border-[#d4af37]",
    selectTrigger:
      "bg-[#6a4b1b] border border-[#9e7c31] text-[#f0e4c1] focus:ring-[#d4af37] focus:border-[#d4af37]",
    selectContent: "bg-[#3e2f0f] text-[#f0e4c1]",
    buttonPrimary:
      "bg-[#a36d00] hover:bg-[#d4af37] focus:ring-[#d4af37] text-[#42210b]",
    buttonSecondary:
      "bg-[#3b2e08] text-[#d4af37] hover:bg-[#a36d00]",
    title: "text-[#d4af37]",
  },
};

 const styles = tierStyles[form.tier || "T1"]; // fallback to T1 if tier missing

return (
  <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
    <DialogContent
      className={`max-w-lg rounded-lg shadow-lg ${styles.modal}`}
    >
      <DialogHeader>
        <DialogTitle className={`text-2xl font-semibold ${styles.title}`}>
          Edit Blueprint
        </DialogTitle>
      </DialogHeader>

      <form onSubmit={handleSubmit} className="space-y-6">
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
            className={styles.input}
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
            className={styles.input}
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
            className={styles.input}
          />
        </div>

        <div>
          <Label htmlFor="editBlueprintStation" className={styles.label}>
            Manufacturing Station
          </Label>
          <Input
            id="editBlueprintStation"
            name="station_name"
            value={form.station_name || ""}
            onChange={handleChange}
            className={styles.input}
          />
        </div>

        <div>
          <Label htmlFor="editBlueprintTier" className={styles.label}>
            Tier
          </Label>
          <Select value={form.tier} onValueChange={handleTierChange}>
            <SelectTrigger
              id="editBlueprintTier"
              className={styles.selectTrigger}
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
                className={styles.input}
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
                  className={styles.selectTrigger}
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
