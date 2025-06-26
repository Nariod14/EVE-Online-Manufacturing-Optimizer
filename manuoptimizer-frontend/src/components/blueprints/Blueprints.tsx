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
import { s } from "vitest/dist/chunks/reporters.d.DL9pg5DB.js";
import { Alert, AlertDescription } from "../ui/alert";



export const fetchBlueprints = async (
  setBlueprints: React.Dispatch<React.SetStateAction<Blueprint[]>>,
  setLoading: React.Dispatch<React.SetStateAction<boolean>>
) => {
  if (process.env.NODE_ENV === "development") {
    await waitForMswReady();
  }

  setLoading(true);

  try {
    console.log("MSW ready. Requesting /api/blueprints/blueprints. Fetching blueprints...");
    const res = await fetch("/api/blueprints/blueprints");
    if (!res.ok) throw new Error("Failed to fetch blueprints");

    const data = await res.json();
    setBlueprints(data);
    console.log("Fetched blueprints:", data);
    return data;
  } catch (err) {
    console.error("Fetch error:", err);
    toast.error("Failed to load blueprints");
    return [];
  } finally {
    setLoading(false);
  }
};
export default function BlueprintsPage() {
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingBlueprint, setEditingBlueprint] = useState<Blueprint | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editTier, setEditTier] = useState<"T1" | "T2" | null>(null);
  const [loading, setLoading] = useState(false);
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
  const [statusEl, setStatusEl] = useState<HTMLDivElement | null>(null);
  const [statusMsg, setStatusMsg] = useState<string>("");


  function handleEdit(bp: Blueprint, tier: "T1" | "T2") {
    setEditingBlueprint(bp);
    setEditTier(tier);
    setEditModalOpen(true);
  }

async function handleSave(updated: Blueprint) {
  try {
    const res = await fetch(`/api/blueprints/blueprint/${updated.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    });

    if (!res.ok) {
      console.error("Failed to update blueprint" + res.statusText + res.body);
      throw new Error("Failed to update blueprint");
      
    }

    toast.success("Blueprint updated");

    const freshBlueprints = await fetchBlueprints(setBlueprints, setLoading);

    const freshBlueprint = freshBlueprints.find((bp: Blueprint) => bp.id === updated.id);

    setEditingBlueprint(freshBlueprint ?? null);

    setEditModalOpen(false);
    setEditingBlueprint(null);
  } catch (error) {
    console.error("Error updating blueprint:", error);
  }
}


useEffect(() => {
  console.log("Blueprints state changed:", blueprints);
}, [blueprints]);

  async function handleAddBlueprintSubmit(data: {
    blueprintPaste: string;
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

  const handleUpdate = async () => {
    setStatusMsg("Updating blueprint prices...");
    document.title = "Updating blueprint prices...";

    try {
      const response = await fetch("/api/blueprints/update_prices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        const data = await response.json();
        setStatusMsg(data.message || "Prices updated successfully!");
        fetchBlueprints(setBlueprints, setLoading);
        document.title = "Eve Manufacturing Optimizer";
      } else {
        const errorData = await response.json();
        setStatusMsg(errorData.error || "Failed to update prices.");
      }
    } catch (error) {
      setStatusMsg("Error updating prices: " + error);
    }
  };




  useEffect(() => {
    fetchBlueprints(setBlueprints, setLoading);
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

    <BlueprintsList
      onEdit={handleEdit}
      blueprints={blueprints}
      onSetBlueprints={setBlueprints}
      loading={loading}
      fetchBlueprints={() => fetchBlueprints(setBlueprints, setLoading)}
    />
   <div className="flex flex-col items-center gap-2 px-6 pt-4">
     <Button
       id="update-blueprints-btn"
       className="w-fit text-sm bg-blue-700 hover:bg-blue-800 mx-auto"
       onClick={handleUpdate}
     >
       Update All Blueprint Prices (Cost and Sell)
     </Button>

     {statusMsg && (
       <Alert
         className="
           w-full
           flex
           justify-center
           items-center
           text-blue-300
           font-semibold
           bg-blue-950/60
           border border-blue-700
           rounded-xl
           py-2
           mt-2
           shadow-lg
           animate-in fade-in
           text-center
         "
       >
         <AlertDescription className="w-full text-center justify-center text-blue-300">{statusMsg}</AlertDescription>
       </Alert>
     )}
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
     onSubmit={handleAddBlueprintSubmit}
     onBlueprintAdded={() => {
       console.log("🔁 Running fetchBlueprints after add");
       fetchBlueprints(setBlueprints, setLoading);
     }} />

   </Card>
 );
}
