import { useState } from "react"
import { Material } from "@/types/materials"



export default function Materials() {
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [editingMaterial, setEditingMaterial] = useState<Material | null>(null);


    function handleEdit(material: Material) {
        setEditingMaterial(material);
        setEditModalOpen(true);
    }

     function handleEditClose() {
        setEditModalOpen(false);
        setEditingMaterial(null);
    }

    function handleSave(updated: Material) {
        // PUT to API here, then reload materials
        try{
            fetch(`/api/materials/material/${updated.id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(updated),
            });
        } catch (error) {
            console.error("Error updating material:", error);
        }
        setEditModalOpen(false);
        setEditingMaterial(null);
    }

   

    


    return (
        <div>Materials</div>
    )
}