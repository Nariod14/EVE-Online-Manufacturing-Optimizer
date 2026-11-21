import { useState } from "react";
import { numberToWords } from "../utils/utils";

type OptimizationTotalsProps = {
  data: {
    total_profit: number;
    true_profit_jita: number;
    true_profit_inventory: number;
    invention_cost?: number;
    sales_fees?: number;
    purchase_cost?: number;
    cash_profit?: number;
  };
};

export default function OptimizationTotals({ data }: OptimizationTotalsProps) {
  // Nothing sold means there is no percentage to show (and no dividing by zero)
  const hasSales = data.total_profit > 0;
  // Percent of inventory-aware profit over total sell value
  const percentInventory = hasSales ? (data.true_profit_inventory / data.total_profit) * 100 : 0;
  // Percent of Jita profit over total sell value
  const percentJita = hasSales ? (data.true_profit_jita / data.total_profit) * 100 : 0;

  // These only come from the newer backend
  const hasCostBreakdown =
    data.sales_fees !== undefined || data.purchase_cost !== undefined || data.cash_profit !== undefined;

  function getProfitClass(percent: number): string {
    if (percent < 15) return 'text-red-400'; // Low
    if (percent < 25) return 'text-orange-400'; // Meh

    if (percent < 35) {
      // Ideal zone: lime with soft glow
      return 'text-lime-400 font-semibold shadow-green-400/30 drop-shadow-sm';
    }

    if (percent < 50) {
      // Above target: emerald with stronger glow
      return 'text-emerald-400 font-semibold shadow-lime-400/40 drop-shadow-md after:content-["⭐️"]';
    }

    if (percent < 70) {
      // Jackpot: emerald with light shimmer
      return 'text-green-400 font-bold drop-shadow-[0_0_5px_#34d399] after:content-["🌟"]';
    }

    // God-tier: glowing purple text with sparkle
    return 'text-fuchsia-400 font-extrabold drop-shadow-[0_0_6px_#e879f9] after:content-["✨"]';
  }

  return (
    <div className="rounded-2xl bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 p-6 shadow-xl border border-blue-800 w-full">
      <h3 className="text-2xl text-blue-200 font-bold mb-4">Optimization Summary</h3>
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-6 text-center text-blue-100">
        <Stat title="Total Sell Value" value={data.total_profit} color="text-green-400" />
        <Stat title="True Profit (Jita)" value={data.true_profit_jita} color="text-blue-400" />
        <Stat
          title="True Profit % (Jita)"
          value={percentJita}
          isPercent={true}
          className={getProfitClass(percentJita)}
        />
        <Stat title="True Profit (Inventory)" value={data.true_profit_inventory} color="text-yellow-400" />
        <Stat
          title="True Profit % (Inventory)"
          value={percentInventory}
          isPercent={true}
          className={getProfitClass(percentInventory)}
        />
      </div>

      {hasCostBreakdown && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 text-center text-blue-100 mt-6">
          <Stat title="Sales Fees" value={data.sales_fees ?? 0} color="text-rose-400" />
          <Stat title="Purchases" value={data.purchase_cost ?? 0} color="text-cyan-400" />
          <Stat title="Invention Cost" value={data.invention_cost ?? 0} color="text-purple-400" />
          <Stat title="Cash Profit" value={data.cash_profit ?? 0} color="text-green-400" />
        </div>
      )}

      <div className="mt-4 text-xs text-blue-400 text-center">
        <span className="block">
          <span className="font-bold">True Profit (Jita):</span> Sell value minus fees, invention and every material used, with your own stock counted at its Jita sell price.
        </span>
        <span className="block">
          <span className="font-bold">True Profit (Inventory):</span> The same, but finished items you already had in stock and used as components count as free.
        </span>
        {hasCostBreakdown && (
          <span className="block">
            <span className="font-bold">Cash Profit:</span> Sell value minus fees, purchases and invention. Everything already in your inventory counts as free here.
          </span>
        )}
      </div>
    </div>
  );
}

type StatProps = {
  title: string;
  value: number;
  color?: string;
  isPercent?: boolean;
  className?: string;
};

export function Stat({ title, value, color, isPercent, className }: StatProps) {
  const [shorthand, setShorthand] = useState(false);

  const toggleFormat = () => {
    setShorthand((prev) => !prev);
  };

  return (
    <div
      className="flex flex-col items-center justify-center bg-slate-800 rounded-xl p-4 shadow-md border border-blue-800 hover:shadow-blue-500/40 hover:border-blue-500 transition duration-300 cursor-pointer"
      onClick={toggleFormat}
      title="Click to toggle value format"
    >
      <span className="text-sm text-blue-300">{title}</span>

      <span className={`text-xl font-semibold transition-all duration-200 ${color ?? ""} ${className ?? ""}`}>
        {isPercent
          ? `${value.toFixed(2)}%`
          : shorthand
          ? numberToWords(value as number)
          : `${Math.round(value).toLocaleString()} ISK`}
      </span>
    </div>
  );
}
