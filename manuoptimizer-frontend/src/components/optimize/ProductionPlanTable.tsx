import { ProductionPlanRow } from "@/types/optimize";

type ProductionPlanTableProps = {
  data: Record<string, number>;
  plan?: ProductionPlanRow[];
  className?: string;
};

export default function ProductionPlanTable({ data, plan, className }: ProductionPlanTableProps) {
  const entries = Object.entries(data)
    .filter(([_, qty]) => qty > 0)
    .sort((a, b) => a[0].localeCompare(b[0]));

  if (entries.length === 0) return null;

  // The detailed rows are only there when the backend sends them; fall back to runs only.
  const planByName = new Map((plan ?? []).map((row) => [row.name, row]));
  const detailed = planByName.size > 0;

  return (
      <div className={`rounded-2xl bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 p-4 shadow-xl border border-blue-800 flex flex-col ${className}`}>
          <h3 className="text-xl text-blue-300 font-semibold">Production Plan</h3>
          <h4 className="text-sm text-blue-100 font-semibold mb-2">
            {detailed
              ? "Runs to install for every blueprint. Units made = runs x units per run."
              : "Optimized items to produce and sell"}
          </h4>
          <div className="flex-1 overflow-auto">
              <table className="w-full text-sm text-left text-blue-100 rounded-lg overflow-hidden border border-blue-800 h-full">
                  <thead className="bg-blue-800 text-blue-100">
                      <tr>
                          <th className="px-4 py-2">Blueprint</th>
                          <th className="px-4 py-2 text-right">{detailed ? "Runs" : "Quantity"}</th>
                          {detailed && <th className="px-4 py-2 text-right">Units made</th>}
                      </tr>
                  </thead>
                  <tbody>
                      {entries.map(([bp, qty]) => {
                          const row = planByName.get(bp);
                          return (
                              <tr key={bp} className="border-t border-blue-800">
                                  <td className="px-4 py-1">{bp}</td>
                                  <td className="px-4 py-1 text-right">{qty.toLocaleString()}</td>
                                  {detailed && (
                                      <td className="px-4 py-1 text-right">
                                          {row ? row.units_produced.toLocaleString() : "-"}
                                      </td>
                                  )}
                              </tr>
                          );
                      })}
                  </tbody>
              </table>
          </div>
      </div>
  );
}
