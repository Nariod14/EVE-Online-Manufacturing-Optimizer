'use client';
import { useEffect, useState } from "react";
import { Material } from "@/types/materials";
import { MaterialList } from "./MaterialsList"; // adjust path if needed
import { EditMaterialModal } from "./EditMaterialModal"; // stub for now
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { waitForMswReady } from "@/lib/mswReady";
import { AddMaterialModal } from "./AddMaterialModal";
import { Accordion, AccordionContent, AccordionTrigger } from "../ui/accordion";
import { AccordionItem } from "@radix-ui/react-accordion";


export default function Materials() {
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [editingMaterial, setEditingMaterial] = useState < Material | null > (null);
    const [addModalOpen, setAddModalOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [materials, setMaterials] = useState < Material[] > ([]);


    function handleEdit(material: Material) {
        setEditingMaterial(material);
        setEditModalOpen(true);
    }

    function handleEditClose() {
        setEditingMaterial(null);
        setEditModalOpen(false);
    }
    async function handleSave(updated: Material) {
      try {
        await fetch(`/api/materials/material/${updated.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updated),
        });

        setMaterials((prev) =>
          prev.map((mat) => (mat.id === updated.id ? updated : mat))
        );

        handleEditClose();
      } catch (error) {
        console.error("Error updating material:", error);
      }
    }

    async function handleAddMaterialSubmit(data: { materialsText: string; updateType: "replace" | "add" }) {
      // Here you'll send `data.materialsText` and `data.updateType` to your backend API
      // For example:
      try {
        const res = await fetch("/api/materials/parse", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Failed to add materials");
        // Optionally refresh your materials list
        await fetchMaterials();
      } catch (error) {
        console.error(error);
        alert("Failed to update materials");
      }
    }

    async function handleDelete(id: number) {
      try {
        const response = await fetch(`/api/materials/material/${id}`, {
          method: "DELETE",
        });

        if (response.ok) {
          setMaterials((prev) => prev.filter((mat) => mat.id !== id));
          console.log("Material deleted successfully.");
        } else {
          console.error("Failed to delete material.");
        }
      } catch (error) {
        console.error("Error deleting material:", error);
      }
    }


    const fetchMaterials = async () => {
    setLoading(true);
    if (process.env.NODE_ENV === 'development') {
        await waitForMswReady(); // only in dev
    }
    try {
        const res = await fetch("/api/materials/materials");
        if (!res.ok) throw new Error("Failed to fetch materials");
        const data = await res.json();
        setMaterials(data);
        console.log("Fetched materials:", data);
    } catch (err) {
        console.error("Fetch error:", err);
    } finally {
        setLoading(false);
    }
    };

    useEffect(() => {
      console.log("Materials state changed:", materials);
    }, [materials]);

    useEffect(() => {
      fetchMaterials();
    }, []);


    return (
      <>
        <Card className="h-full rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-2xl w-full">
          <CardHeader className="px-6 pb-2">
            <div className="flex items-center justify-between">
              <div className="flex flex-col justify-center">
                <CardTitle className="text-2xl text-blue-100">Available Materials</CardTitle>
                <CardDescription className="text-blue-400">View and Manage Materials</CardDescription>
              </div>
              <Button
                onClick={() => setAddModalOpen(true)}
                className="bg-gradient-to-r from-blue-700 via-blue-900 to-blue-800 text-white hover:from-blue-800 hover:to-blue-900 relative top-[5px] left-[-30px] scale-125"
              >
                + Add Materials
              </Button>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            <Accordion type="single" collapsible defaultValue="materials">
              <AccordionItem
                value="materials"
                className="border-none bg-slate-900/60 rounded-xl overflow-hidden"
              >
                <AccordionTrigger className="text-blue-200 text-lg font-bold tracking-wide rounded-xl px-4 py-3 bg-blue-900/80 hover:bg-blue-800/80 hover:no-underline shadow transition-all">
                  View Materials Table (Split by Category)
                </AccordionTrigger>

                <AccordionContent className="bg-slate-900/80 px-2 pb-4 pt-2 rounded-b-xl space-y-4">
                  <p id="update-status" className="text-sm text-gray-400 text-center" />

                  <MaterialList
                    materials={materials}
                    loading={loading}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                  />

                  <div className="flex justify-center">
                    <Button
                      id="update-materials-btn"
                      className="text-sm bg-blue-700 hover:bg-blue-800"
                      onClick={async () => {
                        const statusEl = document.getElementById("update-status");
                        if (statusEl) statusEl.textContent = "Updating material info...";
                        try {
                          const response = await fetch("/api/materials/update_material_info", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                          });
                          if (response.ok) {
                            const data = await response.json();
                            if (statusEl)
                              statusEl.textContent = data.message || "Material info updated successfully!";
                            fetchMaterials();
                          } else {
                            const errorData = await response.json();
                            if (statusEl)
                              statusEl.textContent = errorData.ERROR || "Failed to update material info.";
                          }
                        } catch (error: any) {
                          if (statusEl)
                            statusEl.textContent = "Error updating material info: " + error.message;
                        }
                      }}
                    >
                      Update Material Info (TypeID and Category)
                    </Button>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>

        {/* Modals */}
        <AddMaterialModal
          open={addModalOpen}
          onClose={() => setAddModalOpen(false)}
          onSubmit={handleAddMaterialSubmit}
        />
        {editingMaterial && (
          <EditMaterialModal
            material={editingMaterial}
            open={editModalOpen}
            onClose={handleEditClose}
            onSave={handleSave}
          />
        )}
      </>
    );
    }