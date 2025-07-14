type DependenciesTableProps = {
  data: Record<string, number>;
  className?: string
};

export default function DependenciesTable({ data, className }: DependenciesTableProps) {
  if (!data || Object.keys(data).length === 0) return null;

  const entries = Object.entries(data).sort((a, b) => a[0].localeCompare(b[0]));

  return (
      <div className={`rounded-2xl bg-gradient-to-br from-yellow-950 via-slate-850 to-slate-950 p-4 shadow-xl border border-yellow-800 flex flex-col ${className}`}>
          <h3 className="text-xl text-yellow-300 font-semibold">Required Component Production</h3>
          <h4 className="text-sm text-yellow-100 font-semibold mb-2">Items (materials with blueprints) needed for the production plan</h4>
          <div className="flex-1 overflow-auto">
              <table className="w-full text-sm text-left text-yellow-100 rounded-lg overflow-hidden border border-yellow-800 h-full">
                  <thead className="bg-yellow-800 text-yellow-100">
                      <tr>
                          <th className="px-4 py-2">Component</th>
                          <th className="px-4 py-2">Quantity Needed</th>
                      </tr>
                  </thead>
                  <tbody>
                      {entries.map(([component, qty]) => (
                          <tr key={component} className="border-t border-yellow-800">
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
