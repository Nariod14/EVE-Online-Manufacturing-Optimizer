import { MarginalValue } from "@/types/optimize";

type RestockPriorityProps = {
  items: MarginalValue[];
  className?: string;
};

export default function RestockPriority({ items, className }: RestockPriorityProps) {
  if (!items || items.length === 0) return null;

  const rows = [...items].sort((a, b) => b.ratio - a.ratio);

  return (
    <div className={`rounded-2xl bg-gradient-to-br from-purple-950 via-slate-900 to-slate-950 p-4 shadow-xl border border-purple-800 w-full ${className ?? ""}`}>
      <h3 className="text-xl text-purple-300 font-semibold">Restock First</h3>
      <h4 className="text-sm text-purple-100 font-semibold mb-2">
        Materials that ran out and held this plan back. One more unit of each would add more profit than it costs, so buy the ones at the top first.
      </h4>
      <div className="overflow-auto">
        <table className="w-full text-sm text-left text-purple-100 rounded-lg overflow-hidden border border-purple-800">
          <thead className="bg-purple-800 text-purple-100">
            <tr>
              <th className="px-4 py-2">Material</th>
              <th className="px-4 py-2 text-right">Worth to the plan (per unit)</th>
              <th className="px-4 py-2 text-right">Price on record</th>
              <th className="px-4 py-2 text-right">Worth / price</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} className="border-t border-purple-800">
                <td className="px-4 py-1">{row.name}</td>
                <td className="px-4 py-1 text-right">{row.value.toLocaleString()}</td>
                <td className="px-4 py-1 text-right">{row.market_price.toLocaleString()}</td>
                <td className="px-4 py-1 text-right font-semibold text-purple-300">{row.ratio.toFixed(2)}x</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
