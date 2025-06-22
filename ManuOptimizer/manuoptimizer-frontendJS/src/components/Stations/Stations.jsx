import React, { useState, useEffect } from "react";
import { Button, Card, CardContent } from "@shadcn/ui";
import StationModal from "./StationModal"; // Used for editing stations
import AddStationModal from "./AddStationModal"; // Add new stations
import EditStationModal from "./EditStationModal"; // Edit individual station info

export default function Stations() {
    const [stations, setStations] = useState([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showStationModal, setShowStationModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [selectedStation, setSelectedStation] = useState(null);

    useEffect(() => {
        fetchStations();
    }, []);

    const fetchStations = async () => {
        try {
            const res = await fetch("/api/stations");
            const data = await res.json();
            setStations(data);
        } catch (err) {
            console.error("Failed to fetch stations", err);
        }
    };

    const handleAddClick = () => setShowAddModal(true);

    const handleEditClick = (station) => {
        setSelectedStation(station);
        setShowEditModal(true);
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure?")) return;
        try {
            const res = await fetch(`/api/stations/${id}`, {
                method: "DELETE",
            });
            if (!res.ok) throw new Error("Delete failed");
            setStations((prev) => prev.filter((s) => s.id !== id));
        } catch (err) {
            alert("Failed to delete station");
        }
    };

    return (
        <div className="px-6 py-4">
            <div className="text-center mb-6">
            <Button onClick={() => setShowStationModal(true)} className="bg-blue-500 text-white hover:bg-blue-600">
            Manage Stations
            </Button>

            </div>

            {showStationModal && (
            <StationModal
                onClose={() => setShowStationModal(false)}
                stations={stations}
                onUpdate={fetchStations}
            />
            )}

            {showAddModal && (
                <AddStationModal
                    onClose={() => setShowAddModal(false)}
                    onAdded={() => {
                        fetchStations();
                        setShowAddModal(false);
                    }}
                />
            )}

            {showEditModal && selectedStation && (
                <EditStationModal
                    station={selectedStation}
                    onClose={() => {
                        setSelectedStation(null);
                        setShowEditModal(false);
                    }}
                    onUpdated={fetchStations}
                />
            )}
        </div>
    );
}
