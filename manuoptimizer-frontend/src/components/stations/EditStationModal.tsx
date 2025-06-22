import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Station } from "@/types/stations";


type EditStationModalProps = { 
    open: boolean;
    onOpenChange: (open: boolean) => void;
    station: Station | null;
    onStationUpdate?: (updated: Station) => void;
};

export default function EditStationModal({
    open,
    onOpenChange,
    station,
    onStationUpdate,
  }: EditStationModalProps) {
    const [stationName, setStationName] = useState("");
    const [stationId, setStationId] = useState("");
    const [status, setStatus] = useState < null | {
        success: boolean;message: string
    } > (null);
    const[loading, setLoading] = useState(false);

    useEffect(() => {
        if (station){
            setStationName(station.name);
            setStationId(station.station_id.toString());
            setStatus(null);
        } else {
            setStationName("");
            setStationId("");
            setStatus(null);
            return;
        }
    }, [station, open]);

    if (!station) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setStatus(null);

        if (!stationName.trim() || !stationId.trim()) {
            setStatus({
                success: false,
                message: "Name and Station ID cannot be empty"
            });
            setLoading(false);
            return;
        }

        try {
            const response = await fetch(`/api/stations/${station.id}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: stationName.trim(),
                    station_id: parseInt(stationId, 10),
                }),
            });

            if (response.ok) {
                setStatus({
                    success: true,
                    message: "✅ Station updated successfully!"
                });
                if (onStationUpdate) {
                    onStationUpdate({
                      ...station,
                      name: stationName,
                      station_id: parseInt(stationId, 10),
                    });
                  }
                setTimeout(() => onOpenChange(false), 1500);
            } else{
                const err = await response.json();
                setStatus({
                    success: false,
                    message: `❌ Error updating station: ${err.error || "Unknown error"}`
                });
            }
        } catch (error) {
            setStatus({
                success: false,
                message: `❌ Error updating station: ${error instanceof Error ? error.message : "Unknown error"}`
            });
        } finally {
            setLoading(false);
        }
    }

    const handleClose = () => {
        setStatus(null);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={handleClose}>
            <DialogContent className="max-w-md bg-slate-900 text-blue-100 border border-blue-700">
            <DialogHeader>
                <DialogTitle className="text-blue-300">Edit Station</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                <Label htmlFor="editStationName" className="font-semibold text-blue-200">
                    Name
                </Label>
                <Input
                    id="editStationName"
                    value={stationName}
                    onChange={e => setStationName(e.target.value)}
                    required
                    className="bg-slate-800 text-blue-100 border-blue-700 mt-1"
                />
                </div>
                <div>
                <Label htmlFor="editStationStationId" className="font-semibold text-blue-200">
                    Station ID
                </Label>
                <Input
                    id="editStationStationId"
                    type="number"
                    value={stationId}
                    onChange={e => setStationId(e.target.value)}
                    required
                    className="bg-slate-800 text-blue-100 border-blue-700 mt-1"
                />
                </div>
                {status && (
                <div className={`mt-2 font-semibold ${status.success ? "text-green-400" : "text-red-400"}`}>
                    {status.message}
                </div>
                )}
                <DialogFooter className="gap-2">
                <Button
                    type="submit"
                    disabled={loading}
                    className="bg-gradient-to-r from-blue-700 via-blue-900 to-blue-800 text-white font-bold"
                >
                    {loading ? "Saving..." : "Save"}
                </Button>
                <Button
                    type="button"
                    variant="secondary"
                    onClick={handleClose}
                    className="bg-slate-700 text-blue-200"
                >
                    Cancel
                </Button>
                </DialogFooter>
            </form>
            </DialogContent>
        </Dialog>
        );
    
    
}



            
            

