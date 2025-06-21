import { useState } from "react";
import { numberToWords } from "../utils/utils";

type OptimizationTotalsProps = {
  data: {
    total_profit: number;
    true_profit: number;
  };
};

export default function OptimizationTotals({ data }: OptimizationTotalsProps) {
  const percent = (data.true_profit / data.total_profit) * 100;


  

  function formatISK(value: number) {
    return value.toLocaleString("en-US") + " ISK";
  }

  function getProfitColor(percent: number) {
    if (percent < 20) return 'text-red-400';
    if (percent < 35) return 'text-orange-400';
    if (percent < 50) return 'text-yellow-400';
    if (percent < 70) return 'text-green-400';
    return 'text-blue-400';
  }

  return (
    <div className="rounded-2xl bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 p-6 shadow-xl border border-blue-800 w-full">
      <h3 className="text-2xl text-blue-200 font-bold mb-4">Optimization Summary</h3>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center text-blue-100">
       <Stat title="Total Profit" value={data.total_profit} color="text-green-400" />
       <Stat title="True Profit" value={data.true_profit} color="text-green-400" />
        <Stat title="True Profit %" value={percent} color={getProfitColor(percent)} isPercent={true} />      
        </div>
    </div>
  );
}

type StatProps = {
  title: string;
  value: number;
  color: string;
  isPercent?: boolean;
};

export function Stat({ title, value, color, isPercent }: StatProps) {
    const [shorthand, setShorthand] = useState(false);

    const toggleFormat = () => {
        setShorthand((prev) => !prev);
    }

  return (
    <div
      className="flex flex-col items-center justify-center bg-slate-800 rounded-xl p-4 shadow-md border border-blue-800 hover:shadow-blue-500/40 hover:border-blue-500 transition duration-300 cursor-pointer"
      onClick={toggleFormat}
      title="Click to toggle value format"
    >
      <span className="text-sm text-blue-300">{title}</span>
      <span className={`text-xl font-semibold ${color} transition-all duration-200`}>
        {isPercent ? `${value.toFixed(2)}%` : (shorthand ? numberToWords(value as number) : value.toLocaleString())} ISK
      </span>
      
    </div>
  );
}