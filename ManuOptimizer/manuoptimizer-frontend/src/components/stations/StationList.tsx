import type { Station } from "@/types/stations";
import { Button } from "@/components/ui/button";


type StationListProps = {
    stations: Station[];
    loading ? : boolean;
    error ? : string | null;
    onEdit ? : (station: Station) => void;
    onDelete ? : (stationId: number) => void;
};
export default function StationList({
    stations,
    loading = false,
    error = null,
    onEdit,
    onDelete,
}: StationListProps)  {
  if (loading) {
    return <div className="text-blue-200 p-6 text-center">Loading stations...</div>
  }

  if (error) {
    return <div className="text-red-400 p-6 text-center">{error}</div>
  }

  if (!stations.length) {
    return <div className="text-blue-400 p-6 text-center">No stations added yet.</div>
  }

  return (
    <table className="w-full text-left border-separate border-spacing-y-2">
      <thead>
        <tr>
          <th className="pr-2 py-2 text-blue-400">Name</th>
          <th className="pr-2 py-2 text-blue-400">ID</th>
          <th className="pr-2 py-2 text-blue-400 text-center">Actions</th>
        </tr>
      </thead>
      <tbody>
        {stations.map((station) => (
          <tr
            key={station.id}
            className="bg-slate-800/80 hover:bg-blue-900/50 transition rounded-xl"
          >
            <td className="pr-2 py-2 rounded-l-xl font-semibold text-blue-100">
              {station.name}
            </td>
            <td className="pr-2 py-2 text-blue-300">{station.station_id}</td>
            <td className="pr-2 py-2 rounded-r-xl flex gap-2 justify-center">
              {onEdit && (
                <Button
                  size="sm"
                  variant="secondary"
                  className="bg-blue-700 text-white hover:bg-blue-800 transition"
                  onClick={() => onEdit(station)}
                >
                  Edit
                </Button>
              )}
              {onDelete && (
                <Button
                  size="sm"
                  variant="destructive"
                  className="hover:bg-red-700 transition"
                  onClick={() => onDelete(station.id)}
                >
                  Delete
                </Button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}