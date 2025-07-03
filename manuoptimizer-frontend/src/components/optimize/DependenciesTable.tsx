type DependenciesTableProps = {
  data: Record<string, number>;
};

export default function DependenciesTable({ data }: DependenciesTableProps) {
  if (!data || Object.keys(data).length === 0) return null;

  const entries = Object.entries(data).sort((a, b) => a[0].localeCompare(b[0]));

  return (
    <div   className="rounded-2xl bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 p-4 shadow-xl border border-blue-800 w-full">
      <h3 className="text-xl text-blue-300 font-semibold">Required Component Production</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-blue-100 rounded-lg overflow-hidden border border-blue-800">
          <thead className="bg-blue-800 text-blue-100">
            <tr>
              <th className="px-4 py-2">Component</th>
              <th className="px-4 py-2">Quantity Needed</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([component, qty]) => (
              <tr key={component} className="border-t border-blue-800">
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
