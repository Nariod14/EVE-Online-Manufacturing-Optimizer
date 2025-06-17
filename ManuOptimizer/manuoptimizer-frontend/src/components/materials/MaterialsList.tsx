import { useEffect, useState } from "react";
import { Material } from "@/types/materials";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react"; // optional spinner icon
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../ui/accordion";
import { waitForMswReady } from "@/lib/mswReady";

interface GroupedMaterials {
    [category: string]: Material[];
}
interface MaterialListProps {
    materials: Material[];
    loading: boolean;
    onEdit: (material: Material) => void;
    onDelete: (id: number) => void;
}
    
export function MaterialList({ materials, loading, onEdit, onDelete }: MaterialListProps) {

  const grouped: Record<string, Material[]> = {};
  for (const mat of materials) {
    const cat = mat.category || "Other";
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(mat);
  }

  console.log("Rendering MaterialList with materials:", materials);

  return (
    
    <div className="space-y-4">
        {loading ? (
          <div className="flex items-center space-x-2 text-gray-400 animate-pulse">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Loading materials...</span>
          </div>
        ) : Object.keys(grouped).length === 0 ? (
          <p className="text-sm text-gray-400">No materials found.</p>
        ) : (
          <Accordion type="multiple" className="w-full space-y-2">
            {Object.entries(grouped)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([cat, mats]) => (
                <AccordionItem key={cat} value={cat}>
                  <AccordionTrigger className="text-blue-400 hover:no-underline text-left">
                    <span className="text-lg font-semibold">{cat}</span>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="rounded-md border text-stone-100 border-blue-900 overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-slate-800">
                          <tr>
                            <th className="text-left py-2 px-3 text-blue-300">Name</th>
                            <th className="text-left py-2 px-3 text-blue-300">Quantity</th>
                            <th className="text-left py-2 px-3 text-blue-300">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {mats.map((mat) => (
                            <tr key={mat.id} className="border-t border-blue-900">
                              <td className="py-2 px-3">{mat.name}</td>
                              <td className="py-2 px-3">{mat.quantity}</td>
                              <td className="py-2 px-3 space-x-2">
                                <Button
                                  className="bg-blue-700 hover:bg-blue-800 text-white"
                                  size="sm"
                                  onClick={() => onEdit(mat)}
                                >
                                  Edit
                                </Button>
                                <Button
                                  className="bg-red-700 hover:bg-red-900 text-white"
                                  size="sm"
                                  onClick={() => onDelete(mat.id)}
                                >
                                  Delete
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
          </Accordion>
        )}
    </div>
  );
}