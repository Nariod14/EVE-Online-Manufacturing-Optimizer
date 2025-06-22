'use client';
import { useEffect, useState } from "react";
import BlueprintsList from "@/components/blueprints/BlueprintList";
import { EditBlueprintModal } from "@/components/blueprints/EditBlueprintModal";
import type { Blueprint } from "@/types/blueprints";
import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";
import AddBlueprintModal from "./AddBlueprintModal";
import { Button } from "../ui/button";
import { waitForMswReady } from "@/lib/mswReady";
import { toast } from "sonner";

export default function BlueprintsPage() {
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingBlueprint, setEditingBlueprint] = useState<Blueprint | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editTier, setEditTier] = useState<"T1" | "T2" | null>(null);
  const [loading, setLoading] = useState(false);
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);

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

  async function handleAddBlueprintSubmit(data: {
    materials: string;
    sell_price: number;
    material_cost: number;
    tier: "T1" | "T2";
    invention_materials?: string;
    invention_chance?: number;
    runs_per_copy?: number;
  }) {
    try {
      const res = await fetch("/api/blueprints/blueprints", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to add blueprint");
      const response = await res.json();
      if (response.message) {
        toast.success(response.message);
      } else {
        toast.error(response.error);
      }
    } catch (error) {
      console.error(error);
      alert("Failed to update blueprint");
    }
  }

  const fetchBlueprints = async () => {
    setLoading(true);
    if (process.env.NODE_ENV === 'development') {
      await waitForMswReady(); // only in dev
    }
    try {
      const res = await fetch("/api/blueprints/blueprint");
      if (!res.ok) throw new Error("Failed to fetch blueprints");
      const data = await res.json();
      setBlueprints(data);
      console.log("Fetched blueprints:", data);
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBlueprints();
  }, []);

 return (
   <Card className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-2xl w-full ">
    <CardHeader className="px-6 pb-2">
      <div className="flex items-center justify-between">
        <div className="flex flex-col justify-center">
          <CardTitle className="text-2xl text-blue-100">Blueprints Overview</CardTitle>
          <CardDescription className="text-blue-400">View and Manage Blueprints</CardDescription>
        </div>
        <Button
          onClick={() => setAddModalOpen(true)}
          className="bg-gradient-to-r from-blue-700 via-blue-900 to-blue-800 text-white hover:from-blue-800 hover:to-blue-900 relative top-[10px] left-[-35px] scale-125"
        >
          + Add Blueprints
        </Button>
      </div>
    </CardHeader>

     <BlueprintsList blueprints={blueprints} onEdit={handleEdit} />
     <div className="flex flex-col items-start gap-2 px-6 pt-4">
       <Button
         id="update-blueprints-btn"
         className="w-fit text-sm bg-blue-700 hover:bg-blue-800 mx-auto"
         onClick={async () => {
           const statusEl = document.getElementById("update-blueprints-status");
           if (statusEl) statusEl.textContent = "Updating blueprint prices...";

           try {
             const response = await fetch("/api/blueprints/update_prices", {
               method: "POST",
               headers: { "Content-Type": "application/json" },
             });

             if (response.ok) {
               const data = await response.json();
               if (statusEl) statusEl.textContent = data.message || "Prices updated successfully!";
               fetchBlueprints();
             } else {
               const errorData = await response.json();
               if (statusEl) statusEl.textContent = errorData.error || "Failed to update prices.";
             }
           } catch (error: any) {
             if (statusEl) statusEl.textContent = "Error updating prices: " + error.message;
           }
         }}
       >
         Update All Blueprint Prices (Cost and Sell)
       </Button>

       <div id="update-blueprints-status" className="text-sm text-blue-400 font-semibold" />
     </div>

     <EditBlueprintModal
       open={editModalOpen}
       blueprint={editingBlueprint}
       tier={editTier}
       onClose={() => setEditModalOpen(false)}
       onSave={handleSave}
     />
     <AddBlueprintModal open={addModalOpen} 
     onClose={() => setAddModalOpen(false) 
     } 
     onSubmit={handleAddBlueprintSubmit
     } />
   </Card>
 );
}
