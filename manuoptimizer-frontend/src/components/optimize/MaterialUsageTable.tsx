
type MaterialUsage = {
  used: number;
  remaining: number;
  category?: string;
};

type Props = {
  usage: Record<string, MaterialUsage>;
};

const knownMinerals = [
  "Tritanium", "Pyerite", "Mexallon", "Isogen", "Nocxium",
  "Zydrine", "Megacyte", "Morphite"
];

const CATEGORY_ORDER = [
  "Minerals", "Components", "Items", "Invention Materials",
  "Reaction Materials", "Salvaged Materials", "Planetary Materials",
  "Fuel", "Other"
];

export default function MaterialUsageByCategory({ usage }: Props) {
  const categorized: Record<string, Record<string, MaterialUsage>> = {};

  for (const material in usage) {
    const info = usage[material];
    let category = info.category?.trim() ?? "Other";
    if (knownMinerals.includes(material)) category = "Minerals";
    if (!CATEGORY_ORDER.includes(category)) category = "Other";

    if (!categorized[category]) categorized[category] = {};
    categorized[category][material] = info;
  }

  return (
    <div>
  <h3 className="text-xl text-blue-300 font-semibold mb-4">Material Usage by Category</h3>

  {CATEGORY_ORDER.map((category) => {
    const materials = categorized[category];
    if (!materials) return null;

    const entries = Object.entries(materials);

    return (
      <div key={category} className="mt-6">
        <h4 className="text-blue-200 text-lg font-semibold mb-2">{category}</h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {entries.map(([name, info]) => {
            const usagePercent = info.used / (info.used + info.remaining || 1);
            const usageColor =
              usagePercent > 1
                ? "bg-red-800"
                : usagePercent > 0.9
                ? "bg-yellow-800"
                : "bg-blue-800";

            return (
              <div
                key={name}
                className={`rounded-xl p-4 shadow-md border border-blue-700 bg-slate-900 hover:shadow-blue-500/40 transition`}
              >
                <div className="font-bold text-blue-100">{name}</div>
                <div className="text-sm text-blue-300">Used: {info.used.toLocaleString()}</div>
                <div
                  className={`text-sm ${
                    info.remaining < 0 ? "text-red-400 font-bold" : "text-blue-400"
                  }`}
                >
                  Remaining: {info.remaining.toLocaleString()}
                </div>

                <div className="mt-2 h-2 w-full bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${usageColor}`}
                    style={{ width: `${Math.min(100, usagePercent * 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  })}
</div>

  );
}
