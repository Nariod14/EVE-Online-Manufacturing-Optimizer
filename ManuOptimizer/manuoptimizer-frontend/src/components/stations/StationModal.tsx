'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { Station } from "@/types/stations";

type StationModalProps = {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    stations: Station[];
    loading: boolean;
    error: string | null;
    onEditStation: (station: Station) => void;
    onDeleteStation ? : (stationId: number) => void; // Optional, for future delete logic
};
export default function StationModal({
    open,
    onOpenChange,
    stations,
    loading,
    error,
    onEditStation,
    onDeleteStation,
}: StationModalProps) {
    return (<Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg bg-slate-900 text-blue-100 border border-blue-700">
        <DialogHeader>
          <DialogTitle className="text-blue-300">Stations</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 max-h-[50vh] overflow-y-auto">
          {loading && <div>Loading stations...</div>}
          {error && <div className="text-red-400">{error}</div>}
          {!loading && !error && stations.length === 0 && (
            <div className="text-blue-400">No stations added yet.</div>
          )}
          {!loading && !error && stations.length > 0 && (
            <table className="w-full text-left border-separate border-spacing-y-2">
              <thead>
                <tr>
                  <th className="pr-2">Name</th>
                  <th className="pr-2">ID</th>
                  <th className="pr-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {stations.map(station => (
                  <tr key={station.id} className="bg-slate-800 rounded">
                    <td className="pr-2">{station.name}</td>
                    <td className="pr-2">{station.station_id}</td>
                    <td className="flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="bg-blue-700 text-white"
                        onClick={() => onEditStation(station)}
                      >
                        Edit
                      </Button>
                      {onDeleteStation && (
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => onDeleteStation(station.id)}
                        >
                          Delete
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);
}