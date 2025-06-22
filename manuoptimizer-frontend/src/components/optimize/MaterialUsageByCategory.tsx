import { useState } from "react";
import { cn } from "@/lib/utils"; // If you're using shadcn utils
import { ChevronDown, ChevronRight } from "lucide-react";

type MaterialUsage = {
  used: number;
  remaining: number;
  category?: string;
};

type Props = {
  usage: Record<string, MaterialUsage>;
};

const knownMinerals = [
  "Tritanium", "Pyerite", "Mexallon", "Isogen",
  "Nocxium", "Zydrine", "Megacyte", "Morphite",
];

const CATEGORY_ORDER = [
  "Minerals", "Components", "Items", "Invention Materials",
  "Reaction Materials", "Salvaged Materials", "Planetary Materials",
  "Fuel", "Other"
];

function getUsageColor(percent: number) {
  if (percent >= 200) return "text-red-900";
  if (percent >= 150) return "text-red-700";
  if (percent >= 120) return "text-orange-700";
  if (percent >= 100) return "text-orange-500";
  if (percent >= 80) return "text-yellow-500";
  if (percent >= 60) return "text-green-500";
  if (percent >= 40) return "text-green-300";
  return "text-blue-300";
}
function getUsageBarColor(percent: number): string {
  if (percent >= 200) return "bg-red-9000";
  if (percent >= 180) return "bg-red-800";
  if (percent >= 160) return "bg-red-700";
  if (percent >= 140) return "bg-red-600";
  if (percent >= 120) return "bg-red-500";
  if (percent >= 100) return "bg-red-400"; // Added a new range for 100-120
  if (percent >= 90) return "bg-orange-400";
  if (percent >= 70) return "bg-yellow-500";
  if (percent >= 50) return "bg-yellow-200";
  if (percent >= 30) return "bg-green-300";
  return "bg-green-400";
}

function getRemainingColor(percent: number): string {
  if (percent >= 200) return "text-red-900";
  if (percent >= 180) return "text-red-800";
  if (percent >= 160) return "text-red-700";
  if (percent >= 140) return "text-red-600";
  if (percent >= 120) return "text-red-500";
  if (percent >= 100) return "text-red-400"; // Added a new range for 100-120
  if (percent >= 90) return "text-orange-400";
  if (percent >= 70) return "text-yellow-500";
  if (percent >= 50) return "text-yellow-200";
  if (percent >= 30) return "text-green-300";
  return "text-green-400";
}

export default function MaterialUsageByCategory({ usage }: Props) {
  const categorized: Record<string, Record<string, MaterialUsage>> = {};
  const [open, setOpen] = useState(false);
  for (const material in usage) {
    const info = usage[material];
    let category = info.category?.trim() ?? "Other";
    if (knownMinerals.includes(material)) category = "Minerals";
    if (!CATEGORY_ORDER.includes(category)) category = "Other";

    if (!categorized[category]) categorized[category] = {};
    categorized[category][material] = info;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-2xl text-blue-300 font-semibold mb-2">Material Usage by Category</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {CATEGORY_ORDER.map((category) => {
          const materials = categorized[category];
          if (!materials) return null;

          // const totalUsedAmount = Object.values(materials).reduce((sum, m) => sum + m.used, 0);
          // const totalRemaining = Object.values(materials).reduce((sum, m) => sum + m.remaining, 0);
          const usedCount = Object.values(materials).filter((m) => m.used > 0).length;
          const totalCount = Object.keys(materials).length;

          return (
            <div
              key={category}
              className={cn(
                "rounded-xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border border-blue-800 shadow-md transition-all",
                open ? "ring-2 ring-blue-600 shadow-xl" : "hover:ring-1 hover:ring-blue-600"
              )}
            >
              <div
                className="cursor-pointer flex justify-between items-center p-4"
                onClick={() => setOpen(!open)}
              >
                <div>
                  <h4 className="text-lg text-blue-200 font-bold">{category}</h4>
                  <p className="text-blue-400 text-sm">
                    {totalCount} total kind(s) of {category} — {usedCount} used
                  </p>
                </div>
                <div className="text-blue-400">
                  {open ? <ChevronDown /> : <ChevronRight />}
                </div>
              </div>

              {open && (
                <div className="px-4 pb-4 space-y-2">
                  {/* Table header */}
                  <div className="flex justify-between text-xs text-blue-300 font-semibold border-b border-blue-800 pb-1">
                    <div className="w-1/3">Material</div>
                    <div className="w-1/4 text-right">Used</div>
                    <div className="w-1/4 text-right">Remaining</div>
                    <div className="w-1/5 text-right">Used %</div>
                  </div>

                  {Object.entries(materials)
                    .sort((a, b) => a[0].localeCompare(b[0]))
                    .map(([name, info]) => {
                      const total = info.used + info.remaining;
                      const percent = total > 0 ? (info.used / total) * 100 : 0;
                      const usageColor = getUsageColor(percent);
                      const remainingColor = getRemainingColor(percent);
                      const barWidth = Math.min(percent, 100);

                      return (
                        <div key={name} className="space-y-1">
                          <div className="flex justify-between text-sm text-blue-100">
                            <div className="w-1/3 truncate">{name}</div>
                            <div className="w-1/4 text-rose-400 text-right">{info.used.toLocaleString()}</div>
                            <div className={cn("w-1/4 text-right", remainingColor)}>{info.remaining.toLocaleString()}</div>
                            <div className={`w-1/5 text-right ${remainingColor}`}>{percent.toFixed(1)}%</div>
                          </div>
                          {/* Progress bar */}
                          <div className="h-1 bg-slate-800 rounded overflow-hidden">
                            <div
                              className={cn("h-full transition-all duration-300 ease-in-out", getUsageBarColor(percent))}
                              style={{ width: `${barWidth}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

}
