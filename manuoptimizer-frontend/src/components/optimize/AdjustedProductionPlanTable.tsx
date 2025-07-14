type AdjustedProductionPlanTableProps = {
  data: Record<string, number>;
  className?: string
};

export default function AdjustedProductionPlanTable({ data, className }: AdjustedProductionPlanTableProps) {
  if (!data || Object.keys(data).length === 0) return null;

  const entries = Object.entries(data).sort((a, b) => a[0].localeCompare(b[0]));

  return (
      <div className={`rounded-2xl bg-gradient-to-br from-green-950 via-slate-900 to-slate-950 p-4 shadow-xl border border-green-800 flex flex-col ${className}`}>
          <h3 className="text-xl text-green-300 font-semibold">Adjusted Production Plan</h3>
          <h4 className="text-sm text-green-100 font-semibold mb-2">Removed Items (mats with blueprints) from inventory</h4>
          <div className="flex-1 overflow-auto">
              <table className="w-full text-sm text-left text-green-100 rounded-lg overflow-hidden border border-green-800 h-full">
                  <thead className="bg-green-800 text-green-100">
                      <tr>
                          <th className="px-4 py-2">Component</th>
                          <th className="px-4 py-2">Quantity</th>
                      </tr>
                  </thead>
                  <tbody>
                      {entries.map(([component, qty]) => (
                          <tr key={component} className="border-t border-green-800">
                              <td className="px-4 py-1">{component}</td>
                              <td className="px-4 py-1">{qty.toLocaleString()}</td>
                          </tr>
                      ))}
                  </tbody>
              </table>
          </div>
      </div>
  );
}
