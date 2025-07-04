type MaterialUsage = {
  used: number;
  remaining: number;
};

type BottleneckListProps = {
  materialUsage: Record<string, MaterialUsage>;
};

function getUsagePercentage(used: number, total: number): number {
  return (used / total) * 100;
}

function getUsageBadgeClass(percent: number): string {
  if (percent >= 200) return "bg-red-900 text-red-100";
  if (percent >= 180) return "bg-red-800 text-red-100";
  if (percent >= 160) return "bg-red-700 text-red-50";
  if (percent >= 140) return "bg-red-600 text-red-50";
  if (percent >= 120) return "bg-red-500 text-red-50";
  if (percent >= 100) return "bg-red-400 text-red-100";
  if (percent >= 95)  return "bg-red-300 text-red-900";      // 95-99% = light red
  if (percent >= 90)  return "bg-yellow-400 text-yellow-900"; // 90-94% = yellow
  if (percent >= 70)  return "bg-orange-400 text-orange-900";
  if (percent >= 50)  return "bg-yellow-500 text-yellow-900";
  if (percent >= 30)  return "bg-green-300 text-green-900";
  return "bg-green-400 text-green-900";
}


function getUsageBarColor(percent: number): string {
  if (percent >= 200) return "bg-red-900";
  if (percent >= 180) return "bg-red-800";
  if (percent >= 160) return "bg-red-700";
  if (percent >= 140) return "bg-red-600";
  if (percent >= 120) return "bg-red-500";
  if (percent >= 100) return "bg-red-400";
  if (percent >= 95)  return "bg-red-300";      // 95-99% = light red
  if (percent >= 90)  return "bg-yellow-400";   // 90-94% = yellow
  if (percent >= 70)  return "bg-orange-400";
  if (percent >= 50)  return "bg-yellow-500";
  if (percent >= 30)  return "bg-green-300";
  return "bg-green-400";
}



export default function BottleneckList({ materialUsage }: BottleneckListProps) {
  const bottlenecks = Object.entries(materialUsage)
    .map(([name, usage]) => {
      const total = usage.used + usage.remaining;
      const percent = total > 0 ? getUsagePercentage(usage.used, total) : 0;
      return { name, percent };
    })
    .filter((entry) => entry.percent > 90)
    .sort((a, b) => b.percent - a.percent);

  if (bottlenecks.length === 0) return null;

  return (
    <div className="rounded-2xl bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 p-6 shadow-xl border border-blue-800 w-full">
      <h3 className="text-xl text-blue-300 font-semibold mb-4">Bottleneck Materials</h3>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {bottlenecks.map(({ name, percent }) => (
          <div key={name} className="bg-slate-900/80 border border-blue-800 rounded-xl p-4 shadow hover:shadow-blue-700 transition-all duration-300">
            <div className="flex justify-between items-center mb-1">
              <span className="text-blue-100 font-medium">{name}</span>
              <span className={`text-xs font-bold px-2 py-1 rounded-full ${getUsageBadgeClass(percent)}`}>
                {percent.toFixed(1)}%
              </span>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ease-in-out ${getUsageBarColor(percent)}`}
                style={{ width: `${percent}%` }}
                title={`${percent.toFixed(2)}% used`}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );

}
