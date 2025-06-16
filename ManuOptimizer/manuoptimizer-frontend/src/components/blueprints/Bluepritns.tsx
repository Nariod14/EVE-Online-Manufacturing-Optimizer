'use client';
import { useState } from "react";
import BlueprintsList from "@/components/blueprints/BlueprintList";
import { EditBlueprintModal } from "@/components/blueprints/EditBlueprintModal";
import type { Blueprint } from "@/types/blueprints";

export default function BlueprintsPage() {
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingBlueprint, setEditingBlueprint] = useState<Blueprint | null>(null);
  const [editTier, setEditTier] = useState<"T1" | "T2" | null>(null);

  function handleEdit(bp: Blueprint, tier: "T1" | "T2") {
    setEditingBlueprint(bp);
    setEditTier(tier);
    setEditModalOpen(true);
  }


  function handleSave(updated: Blueprint) {
    // PUT to API here, then reload blueprints
    try {
      fetch(`/api/blueprints/blueprint/${updated.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated),
      });
    } catch (error) {
      console.error("Error updating blueprint:", error);
    }
    setEditModalOpen(false);
    setEditingBlueprint(null);
  }

  return (
    <>
      <BlueprintsList onEdit={handleEdit} />
      <EditBlueprintModal
        open={editModalOpen}
        blueprint={editingBlueprint}
        tier={editTier}
        onClose={() => setEditModalOpen(false)}
        onSave={handleSave}
      />

    </>
  );
}
