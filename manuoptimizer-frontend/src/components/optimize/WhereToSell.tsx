import { Blueprint } from '@/types/blueprints';
import React from 'react';

type WhereToSellProps = {
  productionPlan: Record<string, number>;
  allBlueprints: Blueprint[];
};

function chunk<T>(arr: T[], size: number): T[][] {
  const res = [];
  for (let i = 0; i < arr.length; i += size) {
    res.push(arr.slice(i, i + size));
  }
  return res;
}

export default function WhereToSell({ productionPlan, allBlueprints }: WhereToSellProps) {
  // Group by station name
  const stationsObj: Record<string, { name: string; items: Array<{ name: string; quantity: number }> }> = {};

  Object.entries(productionPlan).forEach(([bpName, quantity]) => {
    if (quantity <= 0) return;

    const blueprint = allBlueprints.find(bp => bp.name === bpName);
    if (!blueprint) return;

    const stationName = blueprint.station_name || "Jita 4-4 Caldari Navy Assembly Plant";

    if (!stationsObj[stationName]) {
      stationsObj[stationName] = {
        name: stationName,
        items: []
      };
    }

    stationsObj[stationName].items.push({
      name: bpName,
      quantity
    });
  });

  const stations = Object.values(stationsObj);

  // Chunk into rows of 3 for display
  const rows = chunk(stations, 3);

  return (
    <div className="w-full">
      <h3 className="text-2xl text-blue-300 font-semibold">Where to Sell</h3>
      <h4 className="text-lg text-blue-300 font-normal mb-2">Which stations to your items</h4>

      {rows.map((row, rowIdx) => {
        if (row.length === 1) {
          return (
            <div key={rowIdx} className="grid grid-cols-3 gap-4 mt-4">
              <div className="col-span-3 flex justify-center">
                <div className="border border-blue-800 rounded-lg p-3 w-2/3">
                  <h5 className="text-lg font-semibold text-blue-200 mb-2">{row[0].name}</h5>
                  <div className="overflow-auto">
                    <table className="w-full text-sm text-left text-blue-100 rounded-lg overflow-hidden border border-blue-800 h-full">
                      <thead className="bg-blue-800 text-blue-100">
                        <tr>
                          <th className="px-4 py-2">Item</th>
                          <th className="px-4 py-2">Qty</th>
                        </tr>
                      </thead>
                      <tbody>
                        {row[0].items.map(item => (
                          <tr key={item.name} className="border-t border-blue-800">
                            <td className="px-4 py-1">{item.name}</td>
                            <td className="px-4 py-1">{item.quantity.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          );
        }

        if (row.length === 2) {
          return (
            <div key={rowIdx} className="grid grid-cols-2 gap-4 mt-4">
              {row.map(station => (
                <div key={station.name} className="border border-blue-800 rounded-lg p-3">
                  <h5 className="text-lg font-semibold text-blue-200 mb-2">{station.name}</h5>
                  <div className="overflow-auto">
                    <table className="w-full text-sm text-left text-blue-100 rounded-lg overflow-hidden border border-blue-800 h-full">
                      <thead className="bg-blue-800 text-blue-100">
                        <tr>
                          <th className="px-4 py-2">Item</th>
                          <th className="px-4 py-2">Qty</th>
                        </tr>
                      </thead>
                      <tbody>
                        {station.items.map(item => (
                          <tr key={item.name} className="border-t border-blue-800">
                            <td className="px-4 py-1">{item.name}</td>
                            <td className="px-4 py-1">{item.quantity.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          );
        }

        // Default: 3 stations
        return (
          <div key={rowIdx} className="grid grid-cols-3 gap-4 mt-4">
            {row.map(station => (
              <div key={station.name} className="border border-blue-800 rounded-lg p-3 col-span-1">
                <h5 className="text-lg font-semibold text-blue-200 mb-2">{station.name}</h5>
                <div className="overflow-auto">
                  <table className="w-full text-sm text-left text-blue-100 rounded-lg overflow-hidden border border-blue-800 h-full">
                    <thead className="bg-blue-800 text-blue-100">
                      <tr>
                        <th className="px-4 py-2">Item</th>
                        <th className="px-4 py-2">Qty</th>
                      </tr>
                    </thead>
                    <tbody>
                      {station.items.map(item => (
                        <tr key={item.name} className="border-t border-blue-800">
                          <td className="px-4 py-1">{item.name}</td>
                          <td className="px-4 py-1">{item.quantity.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        );
      })}

    </div>
  );
}
