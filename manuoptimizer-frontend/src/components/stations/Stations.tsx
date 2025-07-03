"use client";
import {useState,useEffect} from "react";
import {Button} from "@/components/ui/button";
import AddStationModal from "./AddStationModal";
import StationModal from "./StationModal";
import EditStationModal from "./EditStationModal";
import StationList from "./StationList";
import type { Station } from "@/types/stations";
import { toast } from "sonner";
import { waitForMswReady } from "@/lib/mswReady";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../ui/accordion";


// (You’ll create AddStationModal.tsx next)
export default function Stations() {
    // Modal open/close states
    const [addModalOpen, setAddModalOpen] = useState(false);
    const [manageModalOpen, setManageModalOpen] = useState(false);
    const [editModalOpen, setEditModalOpen] = useState(false);
    

    // Station data and selection
    const [stations, setStations] = useState<Station[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [editStation, setEditStation] = useState<Station | null>(null);
    const [mswReady, setMswReady] = useState(false);

    async function fetchStations() {
      setLoading(true);

      if (process.env.NODE_ENV === 'development') {
        await waitForMswReady(); // only in dev
      }

      console.log("MSW ready. Requesting /api/stations");

      try {
        const res = await fetch("/api/stations");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setStations(data);
      } catch (err: any) {
        console.error("Failed to fetch stations:", err);
      } finally {
        setLoading(false);
      }
    }

    useEffect(() => {
      fetchStations();
    }, []);

    const handleEditStation = (station: Station) => {
        setEditStation(station);
        setEditModalOpen(true);
      };

      const handleStationUpdate = async (updatedStation: Station) => {
        try {
          const res = await fetch(`/api/stations/${updatedStation.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: updatedStation.name,
              station_id: updatedStation.station_id,
            }),
          });

          if (!res.ok) {
            throw new Error(`Failed to update station, status ${res.status}`);
          }

          await fetchStations();

        } catch (error) {
          console.error('Error updating station:', error);
        }
      };

      const handleDeleteStation = async (id: number) => {
        if (!window.confirm("Are you sure you want to delete this station?")) return;
      
        try {
          const res = await fetch(`/api/stations/${id}`, { method: "DELETE" });
          if (res.ok) {
            // Option 1: Remove from local state
            setStations((prev) => prev.filter((station) => station.id !== id));
            // Optionally show a toast or alert
            // toast.success("Station deleted!");
          } else {
            const err = await res.json();
            alert("Error: " + (err.error || "Unknown error"));
          }
        } catch (e) {
          alert("Error: " + (e instanceof Error ? e.message : "Unknown error"));
        }
      };
      

     return (
         <>
           <Card className="h-full rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-2xl w-full">
             <CardHeader className="px-6 pb-2">
               <div className="flex items-center justify-between">
                 <div>
                   <CardTitle className="text-2xl text-blue-100">Your Stations</CardTitle>
                   <CardDescription className="text-blue-400">
                     Manage your selling stations. (If none, Jita will be used)
                   </CardDescription>
                 </div>
                 <Button
                   onClick={() => setAddModalOpen(true)}
                   className="bg-gradient-to-r from-blue-700 via-blue-900 to-blue-800 text-white hover:from-blue-800 hover:to-blue-900 scale-120 relative right-2"
                 >
                   + Add Station
                 </Button>
               </div>
             </CardHeader>

             <CardContent className="px-6 pb-6">
               <Accordion type="single" collapsible>
                 <AccordionItem
                   value="stations"
                   className="border-none bg-slate-900/60 rounded-xl overflow-hidden"
                 >
                   <AccordionTrigger className="text-blue-200 text-lg font-bold tracking-wide rounded-xl px-4 py-3 bg-blue-900/80 hover:bg-blue-800/80 hover:no-underline shadow transition-all">
                     View Station List
                   </AccordionTrigger>

                   <AccordionContent className="bg-slate-900/80 px-2 pb-4 pt-2 rounded-b-xl">
                     <StationList
                       stations={stations}
                       loading={loading}
                       error={error}
                       onEdit={handleEditStation}
                       onDelete={handleDeleteStation}
                     />
                   </AccordionContent>
                 </AccordionItem>
               </Accordion>
             </CardContent>
           </Card>

           {/* Modals */}
           <StationModal
             open={manageModalOpen}
             onOpenChange={setManageModalOpen}
             stations={stations}
             loading={loading}
             error={error}
             onEditStation={handleEditStation}
           />

           {editStation && (
             <EditStationModal
               open={editModalOpen}
               onOpenChange={setEditModalOpen}
               station={editStation}
               onStationUpdate={handleStationUpdate}
             />
           )}

           <AddStationModal open={addModalOpen} onOpenChange={setAddModalOpen} />
         </>
       );
     }

