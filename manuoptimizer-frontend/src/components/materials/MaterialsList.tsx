import { Material } from "@/types/materials";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react"; // optional spinner icon
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../ui/accordion";
import { ConfirmDeleteButton } from "../utils/utils";

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

 return (
  <div className="space-y-6">
    {loading ? (
      <div className="flex items-center space-x-2 text-blue-300 animate-pulse">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>Loading materials...</span>
      </div>
    ) : Object.keys(grouped).length === 0 ? (
      <p className="text-sm text-blue-300 italic">No materials found.</p>
    ) : (
      <Accordion type="multiple" className="w-full space-y-4">
        {Object.entries(grouped)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([cat, mats]) => (
            <AccordionItem
              key={cat}
              value={cat}
              className="rounded-2xl border border-blue-800 bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 shadow-lg"
            >
              <AccordionTrigger className="px-4 py-3 text-left text-lg font-semibold text-blue-200 hover:no-underline hover:text-blue-300">
                {cat}
              </AccordionTrigger>
              <AccordionContent className="px-4 pb-4 space-y-3">
                {mats.map((mat) => (
                  <div
                    key={mat.id}
                    className="flex justify-between items-center bg-slate-900/70 hover:bg-blue-900/60 border border-blue-800 rounded-xl px-4 py-2 shadow-sm transition-all"
                  >
                    <div className="flex flex-col">
                      <span className="font-semibold text-blue-100">{mat.name}</span>
                      <span className="text-sm text-blue-300">
                        {mat.quantity.toLocaleString()} units
                      </span>
                    </div>

                    <div className="space-x-2">
                      <Button
                        size="sm"
                        className="bg-blue-700 hover:bg-blue-600 shadow-md hover:shadow-blue-500/30 text-white"
                        onClick={() => onEdit(mat)}
                      >
                        Edit
                      </Button>
                      <ConfirmDeleteButton onDelete={() => onDelete(mat.id)}>
                        Delete
                      </ConfirmDeleteButton>
                    </div>
                  </div>
                ))}
              </AccordionContent>
            </AccordionItem>
          ))}
      </Accordion>
    )}
  </div>
);

}