'use client';

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";


type AddStationModalProps = {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onStationAdded ? : () => void; // Optional: parent can refresh list if needed
};
export default function AddStationModal({
    open,
    onOpenChange,
    onStationAdded,
}: AddStationModalProps) {
    const [stationName, setStationName] = useState("");
    const [stationId, setStationId] = useState("");
    const [status, setStatus] = useState < null | {
        success: boolean;message: string
    } > (null);
    const [loading, setLoading] = useState(false);
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setStatus(null);
        try {
            const response = await fetch("/api/stations", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: stationName.trim(),
                    station_id: parseInt(stationId, 10),
                }),
            });
            const result = await response.json();
            if (response.ok) {
                setStatus({
                    success: true,
                    message: "✅ Station added successfully!"
                });
                setStationName("");
                setStationId("");
                if (onStationAdded) onStationAdded();
            } else {
                setStatus({
                    success: false,
                    message: `❌ ${result.error || "Unknown error"}`
                });
            }
        } catch (err) {
            setStatus({
                success: false,
                message: "❌ Network error"
            });
        } finally {
            setLoading(false);
        }
    };
    const handleClose = () => {
        setStatus(null);
        setStationName("");
        setStationId("");
        onOpenChange(false);
    };
    return (<Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md bg-slate-900 text-blue-100 border border-blue-700">
        <DialogHeader>
          <DialogTitle className="text-blue-300">Add New Station</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="stationName" className="font-semibold text-blue-200">
              Station Name
            </Label>
            <Input
              id="stationName"
              name="stationName"
              placeholder="e.g., Neo Nexus Refinery"
              value={stationName}
              onChange={(e) => setStationName(e.target.value)}
              required
              className="bg-slate-800 text-blue-100 border-blue-700 mt-1"
            />
          </div>
          <div>
            <Label htmlFor="stationId" className="font-semibold text-blue-200">
              Station ID
            </Label>
            <Input
              id="stationId"
              name="stationId"
              type="number"
              placeholder="e.g., 1024012922938"
              value={stationId}
              onChange={(e) => setStationId(e.target.value)}
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
              {loading ? "Adding..." : "Add Station"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              className="bg-slate-700 text-blue-200"
            >
              Close
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>);
}