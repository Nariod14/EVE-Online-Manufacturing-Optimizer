import { useState } from "react";
import { BuyMode, ShoppingListEntry } from "@/types/optimize";
import { numberToWords } from "../utils/utils";

type ShoppingListProps = {
  items: Record<string, ShoppingListEntry>;
  total: number;
  buyMode?: BuyMode; // the mode the backend actually used (result.settings.buy)
  totalVolume?: number; // m3 of everything on the list (result.purchase_volume)
  cargoPerTrip?: number; // hauler m3 per trip, to show how many trips the list takes
  className?: string;
};

const m3 = (v: number) => `${v.toLocaleString(undefined, { maximumFractionDigits: 1 })} m3`;

export default function ShoppingList({ items, total, buyMode, totalVolume, cargoPerTrip, className }: ShoppingListProps) {
  const [copied, setCopied] = useState(false);

  const entries = Object.entries(items)
    .filter(([, entry]) => entry.quantity > 0)
    .sort((a, b) => b[1].cost - a[1].cost);

  if (entries.length === 0) return null;

  // "Name quantity" per line is the format the in-game multibuy window accepts.
  const multibuyText = entries.map(([name, entry]) => `${name} ${entry.quantity}`).join("\n");

  const copyForMultibuy = async () => {
    try {
      await navigator.clipboard.writeText(multibuyText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Could not copy the shopping list:", err);
    }
  };

  return (
    <div className={`rounded-2xl bg-gradient-to-br from-cyan-950 via-slate-900 to-slate-950 p-4 shadow-xl border border-cyan-800 w-full ${className ?? ""}`}>
      <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
        <div>
          <h3 className="text-xl text-cyan-300 font-semibold">Shopping List</h3>
          <h4 className="text-sm text-cyan-100 font-semibold">
            What to buy with your budget, at the prices on record. BUY THESE BEFORE YOU START.
          </h4>
          {buyMode === "all" && (
            <p className="text-xs text-yellow-300 mt-1">
              Made with &quot;Anything with a price&quot;, so your buy list was not used. Switch &quot;Spend it on&quot; to &quot;My buy list&quot; to limit it.
            </p>
          )}
          {buyMode === "list" && (
            <p className="text-xs text-cyan-400 mt-1">Only items on your buy list.</p>
          )}
          {totalVolume !== undefined && totalVolume > 0 && (
            <p className="text-xs text-cyan-200 mt-1">
              Volume: {m3(totalVolume)}
              {cargoPerTrip && cargoPerTrip > 0
                ? `, ${Math.ceil(totalVolume / cargoPerTrip - 1e-9)} trip(s) of ${m3(cargoPerTrip)}`
                : ""}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={copyForMultibuy}
          className="rounded-md border border-cyan-700 bg-cyan-900/60 px-3 py-1 text-sm text-cyan-100 hover:bg-cyan-800 transition"
        >
          {copied ? "Copied!" : "Copy for multibuy"}
        </button>
      </div>
      <div className="overflow-auto">
        <table className="w-full text-sm text-left text-cyan-100 rounded-lg overflow-hidden border border-cyan-800">
          <thead className="bg-cyan-800 text-cyan-100">
            <tr>
              <th className="px-4 py-2">Material</th>
              <th className="px-4 py-2 text-right">Quantity</th>
              <th className="px-4 py-2 text-right">Unit price</th>
              <th className="px-4 py-2 text-right">Volume</th>
              <th className="px-4 py-2 text-right">Cost</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, entry]) => (
              <tr key={name} className="border-t border-cyan-800">
                <td className="px-4 py-1">{name}</td>
                <td className="px-4 py-1 text-right">{entry.quantity.toLocaleString()}</td>
                <td className="px-4 py-1 text-right">{entry.unit_price.toLocaleString()}</td>
                <td className="px-4 py-1 text-right">
                  {entry.volume_m3 === null || entry.volume_m3 === undefined ? "?" : m3(entry.volume_m3)}
                </td>
                <td className="px-4 py-1 text-right">
                  {Math.round(entry.cost).toLocaleString()}{" "}
                  <span className="text-xs text-cyan-400">({numberToWords(entry.cost)})</span>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-cyan-700 bg-cyan-900/40 font-semibold">
              <td className="px-4 py-2" colSpan={3}>Total</td>
              <td className="px-4 py-2 text-right">{totalVolume ? m3(totalVolume) : ""}</td>
              <td className="px-4 py-2 text-right">
                {Math.round(total).toLocaleString()} ISK{" "}
                <span className="text-xs text-cyan-400">({numberToWords(total)})</span>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
