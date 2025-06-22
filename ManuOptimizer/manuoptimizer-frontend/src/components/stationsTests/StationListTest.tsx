"use client";

import { useState } from "react";
import StationList from "@/components/stations/StationList";
import EditStationModal from "@/components/stations/EditStationModal";
import type { Station } from "@/types/stations";

const MOCK_STATIONS: Station[] = [
  { id: 1, name: "Jita IV - Moon 4", station_id: 60003760 },
  { id: 2, name: "Amarr VIII (Oris)", station_id: 60008494 },
  { id: 3, name: "Dodixie IX - Moon 20", station_id: 60011866 },
  { id: 4, name: "Rens VI - Moon 8", station_id: 60004588 },
];

export default function StationListTest() {
  const [stations, setStations] = useState<Station[]>(MOCK_STATIONS);

  // State for modal
  const [editOpen, setEditOpen] = useState(false);
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);

  // Handler for Edit button
  const handleEdit = (station: Station) => {
    setSelectedStation(station);
    setEditOpen(true);
  };

  // Handler for Delete button
  const handleDelete = (stationId: number) => {
    if (confirm("Are you sure you want to delete this station?")) {
      setStations((prev) => prev.filter((s) => s.id !== stationId));
    }
  };

  // Handler for updating a station (simulate update in local state)
  const handleStationUpdated = (updatedStation: Station) => {
    setStations((prev) =>
      prev.map((s) => (s.id === updatedStation.id ? updatedStation : s))
    );
  };

  return (
    <div className="max-w-2xl mx-auto mt-10">
      {/* <h1 className="text-2xl font-bold mb-6 text-blue-200">StationList Test</h1> */}
      <StationList
        stations={stations}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
      {/* Render the EditStationModal */}
      <EditStationModal
        open={editOpen}
        onOpenChange={setEditOpen}
        station={selectedStation}
        // For testing: update local state instead of real API
        onStationUpdate={handleStationUpdated}
      />
    </div>
  );
}
