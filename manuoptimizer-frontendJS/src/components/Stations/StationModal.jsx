import React, { useEffect, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";

// We'll use some Tailwind utility classes directly, or
// create smaller reusable components if needed.

export default function StationModal({ open, setOpen, onUpdated }) {
    // `open` controls modal visibility
    // `setOpen` toggles visibility
    // `onUpdated` callback after update/delete to refresh parent list

    const [stations, setStations] = useState([]);
    const [error, setError] = useState("");

    // Fetch stations when modal opens
    useEffect(() => {
        if (open) {
            fetchStations();
        }
    }, [open]);

    async function fetchStations() {
        try {
            const res = await fetch("/api/stations");
            if (!res.ok) {
                setError("Failed to load stations." + res.status);
                return;
            }
            const data = await res.json();
            setStations(data);
            setError("");
        } catch (err) {
            setError("Failed to load stations." + err);
        }
    }

    // Handle field change locally
    function handleChange(id, field, value) {
        setStations((prev) =>
            prev.map((station) =>
                station.id === id
                    ? {
                          ...station,
                          [field]:
                              field === "station_id" ? Number(value) : value,
                      }
                    : station
            )
        );
    }

    // Save updates to server
    async function handleSave(id) {
        const station = stations.find((s) => s.id === id);
        try {
            const res = await fetch(`/api/stations/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: station.name,
                    station_id: station.station_id,
                }),
            });
            if (!res.ok) throw new Error("Failed to update");
            alert("Station updated successfully!");
            onUpdated?.();
        } catch {
            alert("Update failed!" + res.status);
        }
    }

    // Delete station
    async function handleDelete(id) {
        if (!window.confirm("Are you sure?")) return;
        try {
            const res = await fetch(`/api/stations/${id}`, {
                method: "DELETE",
            });
            if (!res.ok) throw new Error("Failed to delete");
            alert("Station deleted!");
            setStations((prev) => prev.filter((s) => s.id !== id));
            onUpdated?.();
        } catch {
            alert("Delete failed!" + res.status);
        }
    }

    return (
        <Dialog.Root open={open} onOpenChange={setOpen}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/60 data-[state=open]:animate-fadeIn" />
                <Dialog.Content
                    className="fixed top-1/2 left-1/2 max-w-lg w-[90vw] max-h-[85vh] overflow-auto
          rounded-md bg-white p-6 shadow-lg
          -translate-x-1/2 -translate-y-1/2
          focus:outline-none"
                >
                    <Dialog.Title className="text-xl font-semibold mb-4">
                        Stations
                    </Dialog.Title>

                    {error && <p className="text-red-600 mb-2">{error}</p>}

                    {stations.length === 0 ? (
                        <p className="text-gray-400">No stations available.</p>
                    ) : (
                        <div className="space-y-4">
                            {stations.map((station) => (
                                <div
                                    key={station.id}
                                    className="flex items-center space-x-2 border-b border-gray-200 pb-2"
                                >
                                    <input
                                        className="border rounded px-2 py-1 flex-1"
                                        type="text"
                                        value={station.name}
                                        onChange={(e) =>
                                            handleChange(
                                                station.id,
                                                "name",
                                                e.target.value
                                            )
                                        }
                                        aria-label={`Station name for ${station.name}`}
                                    />
                                    <input
                                        className="border rounded px-2 py-1 w-20"
                                        type="number"
                                        value={station.station_id}
                                        onChange={(e) =>
                                            handleChange(
                                                station.id,
                                                "station_id",
                                                e.target.value
                                            )
                                        }
                                        aria-label={`Station ID for ${station.name}`}
                                    />
                                    <button
                                        onClick={() => handleSave(station.id)}
                                        className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 transition"
                                    >
                                        Save
                                    </button>
                                    <button
                                        onClick={() => handleDelete(station.id)}
                                        className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 transition"
                                        aria-label={`Delete station ${station.name}`}
                                    >
                                        Delete
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}

                    <Dialog.Close className="mt-6 inline-block rounded bg-gray-300 px-4 py-2 text-gray-800 hover:bg-gray-400 transition">
                        Close
                    </Dialog.Close>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}
