type ProductionPlanTableProps = {
  data: Record<string, number>;
  className?: string;
};

export default function ProductionPlanTable({ data, className }: ProductionPlanTableProps) {
  const entries = Object.entries(data)
    .filter(([_, qty]) => qty > 0)
    .sort((a, b) => a[0].localeCompare(b[0]));

  if (entries.length === 0) return null;

  return (
      <div className={`rounded-2xl bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 p-4 shadow-xl border border-blue-800 flex flex-col ${className}`}>
          <h3 className="text-xl text-blue-300 font-semibold">Production Plan</h3>
          <h4 className="text-sm text-blue-100 font-semibold mb-2">Optimized items to produce and sell</h4>
          <div className="flex-1 overflow-auto">
              <table className="w-full text-sm text-left text-blue-100 rounded-lg overflow-hidden border border-blue-800 h-full">
                  <thead className="bg-blue-800 text-blue-100">
                      <tr>
                          <th className="px-4 py-2">Blueprint</th>
                          <th className="px-4 py-2">Quantity</th>
                      </tr>
                  </thead>
                  <tbody>
                      {entries.map(([bp, qty]) => (
                          <tr key={bp} className="border-t border-blue-800">
                              <td className="px-4 py-1">{bp}</td>
                              <td className="px-4 py-1">{qty.toLocaleString()}</td>
                          </tr>
                      ))}
                  </tbody>
              </table>
          </div>
      </div>
  );
}
