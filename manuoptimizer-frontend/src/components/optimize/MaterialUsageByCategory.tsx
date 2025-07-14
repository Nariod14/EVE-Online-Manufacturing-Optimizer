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
  savings?: Record<string, { amount: number; category?: string }>;
  expected_invention?: Record<string, number>;
  invention_cost?: number;
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

type InventorySaving = {
  amount: number;
  category?: string;
};


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
  if (percent >= 200) return "bg-red-900";
  if (percent >= 180) return "bg-red-800";
  if (percent >= 160) return "bg-red-700";
  if (percent >= 140) return "bg-red-600";
  if (percent >= 120) return "bg-red-500";
  if (percent >= 100) return "bg-red-400";
  if (percent >= 90)  return "bg-red-300";    // Start red at 90+
  if (percent >= 70)  return "bg-orange-400";
  if (percent >= 50)  return "bg-yellow-500";
  if (percent >= 30)  return "bg-green-300";
  return "bg-green-400";
}

function getRemainingColor(percent: number): string {
  if (percent >= 200) return "text-red-900";
  if (percent >= 180) return "text-red-800";
  if (percent >= 160) return "text-red-700";
  if (percent >= 140) return "text-red-600";
  if (percent >= 120) return "text-red-500";
  if (percent >= 100) return "text-red-400";
  if (percent >= 90)  return "text-red-300";    // Start red at 90+
  if (percent >= 70)  return "text-orange-400";
  if (percent >= 50)  return "text-yellow-500";
  if (percent >= 30)  return "text-green-300";
  return "text-green-400";
}


export default function MaterialUsageByCategory({ usage, savings = {}, expected_invention, invention_cost }: Props) {
  const categorized: Record<string, Record<string, MaterialUsage>> = {};
  const [open, setOpen] = useState(false);
  const [open2, setOpen2] = useState(false);
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
      <div className="mb-4">
        <h3 className="text-2xl text-blue-300 font-semibold">Material Usage by Category</h3>
        <p className="text-lg text-blue-300 font-normal mb-2">See "To be built" and "Inventory Savings" for more details on negative materials.</p>
      </div>
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
      
      {/* To Be Built + Expected Invention + Inventory Savings Section */}
      {/* To Be Built + Expected Invention + Inventory Savings Section */}
      <div className="mt-6">
        {/* First determine which sections have data */}
        {(() => {
          const hasToBeBuilt = Object.entries(usage).some(
            ([_, info]) => info.category === "Items" && info.remaining < 0
          );
          const hasExpectedInvention = expected_invention && Object.keys(expected_invention).length > 0;
          const hasInventorySavings = savings && Object.keys(savings).length > 0;
          const sectionsWithData = [hasToBeBuilt, hasExpectedInvention, hasInventorySavings].filter(Boolean).length;

          return (
            <div className={`flex flex-col md:flex-row gap-4 ${sectionsWithData === 1 ? 'justify-center' : ''}`}>
              {/* To Be Built Section */}
              {hasToBeBuilt && (
                <div className={`${sectionsWithData === 1 ? 'w-full md:w-2/3' : sectionsWithData === 2 ? 'w-full md:w-1/2' : 'w-full md:w-1/3'}`}>
                  <div className="rounded-xl bg-gradient-to-br from-yellow-800/30 to-yellow-900/30 border border-yellow-600 shadow-inner h-full">
                    {/* Your existing To Be Built content goes here */}
                    <div
                      className="cursor-pointer flex justify-between items-center p-4"
                      onClick={() => setOpen2(!open2)}
                    >
                      <div className="flex flex-col w-full">
                        <h4 className="text-lg text-yellow-300 font-semibold pb-2.5 text-center">To Be Built</h4>
                        <h3 className="text-yellow-300 font-semibold mt-2 text-sm text-center">Shortfall from Items</h3>
                      </div>
                      <div className="text-yellow-300">{open2 ? <ChevronDown /> : <ChevronRight />}</div>
                    </div>

                    {open2 && (
                      <div className="px-4 pb-4">
                        <div className="flex justify-between text-xs text-yellow-200 font-semibold border-b border-yellow-600 pb-1">
                          <div className="w-2/3">Material</div>
                          <div className="w-1/3 text-right">Amount</div>
                        </div>
                        <div className="mt-2 space-y-1">
                          {Object.entries(usage)
                            .filter(([_, info]) => info.category === "Items" && info.remaining < 0)
                            .sort(([a], [b]) => a.localeCompare(b))
                            .map(([name, info]) => (
                              <div key={name} className="flex justify-between text-sm text-yellow-100">
                                <div className="w-2/3 truncate">{name}</div>
                                <div className="w-1/3 text-right text-yellow-400">
                                  {Math.abs(info.remaining).toLocaleString()}
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Expected Invention Section */}
              {hasExpectedInvention && (
                <div className={`${sectionsWithData === 1 ? 'w-full md:w-2/3' : sectionsWithData === 2 ? 'w-full md:w-1/2' : 'w-full md:w-1/3'}`}>
                  <div className="rounded-xl bg-gradient-to-br from-purple-800/30 to-purple-950/30 border border-purple-700 shadow-inner relative pb-10 h-full">
                    <div 
                      className="cursor-pointer flex justify-between items-center p-4"
                      onClick={() => setOpen2(!open2)}
                    >
                      <div className="flex flex-col w-full">
                        <h4 className="text-lg text-purple-300 font-semibold text-center">Expected Invention Use</h4>
                        <h4 className="text-sm text-purple-300 font-semibold text-center pb-4">
                          Invention materials needed for planned T2 production
                        </h4>
                      </div>
                      <div className="text-purple-300">
                        {open2 ? <ChevronDown /> : <ChevronRight />}
                      </div>
                    </div>
                    {open2 && expected_invention && (
                      <div className="px-4 pb-4">
                        <div className="flex justify-between text-xs text-purple-200 font-semibold border-b border-purple-600 pb-1">
                          <div className="w-2/3">Material</div>
                          <div className="w-1/3 text-right">Needed</div>
                        </div>
                        <div className="mt-2 space-y-1">
                          {Object.entries(expected_invention)
                            .sort(([a], [b]) => a.localeCompare(b))
                            .map(([name, amount]) => (
                              <div key={name} className="flex justify-between text-sm text-purple-100">
                                <div className="w-2/3 truncate">{name}</div>
                                <div className="w-1/3 text-right text-purple-400">
                                  {amount.toLocaleString()}
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                    {invention_cost !== undefined && (
                      <div className="absolute bottom-0 p-4 bg-purple-800/20 border-t border-purple-700 text-sm text-purple-100 w-full mt-10 pb-1">
                        <div className="flex justify-between">
                          <div className="w-2/3">Total (Expected) Invention Cost:</div>
                          <div className="w-1/3 text-right text-purple-400">
                            {invention_cost.toLocaleString()}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Inventory Savings Section */}
              {hasInventorySavings && (
                <div className={`${sectionsWithData === 1 ? 'w-full md:w-2/3' : sectionsWithData === 2 ? 'w-full md:w-1/2' : 'w-full md:w-1/3'}`}>
                  <div className="rounded-xl bg-gradient-to-br from-emerald-800/30 to-emerald-950/30 border border-emerald-700 shadow-inner h-full">
                    <div
                      className="cursor-pointer flex justify-between items-center p-4"
                      onClick={() => setOpen2(!open2)}
                    > 
                      <div className="flex flex-col w-full">
                        <h4 className={`text-lg text-emerald-300 font-semibold pb-2.5 text-center`}>Inventory Savings</h4>
                        <h4 className="text-sm text-emerald-300 font-semibold text-center">Items (mats with blueprints) used directly from your inventory</h4>
                      </div>
                      <div className="text-emerald-300">{open2 ? <ChevronDown /> : <ChevronRight />}</div>
                    </div>

                    {open2 && (
                      <div className="px-4 pb-4">
                        {Object.entries(
                          Object.entries(savings).reduce((acc, [name, { amount, category = "Other" }]) => {
                            if (!acc[category]) acc[category] = {};
                            acc[category][name] = amount;
                            return acc;
                          }, {} as Record<string, Record<string, number>>)
                        )
                          .sort(([a], [b]) => a.localeCompare(b))
                          .map(([category, materials]) => (
                            <div key={category} className="mb-4">
                              <h5 className="text-emerald-200 font-medium mb-1">{category}</h5>
                              <div className="flex justify-between text-xs text-emerald-300 font-semibold border-b border-emerald-600 pb-1">
                                <div className="w-2/3">Material</div>
                                <div className="w-1/3 text-right">Saved</div>
                              </div>
                              <div className="mt-1 space-y-1">
                                {Object.entries(materials)
                                  .sort(([a], [b]) => a.localeCompare(b))
                                  .map(([name, amount]) => (
                                    <div key={name} className="flex justify-between text-sm text-emerald-100">
                                      <div className="w-2/3 truncate">{name}</div>
                                      <div className="w-1/3 text-right text-emerald-400">
                                        {amount.toLocaleString()}
                                      </div>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })()}
      </div>

    </div>
  );

}
