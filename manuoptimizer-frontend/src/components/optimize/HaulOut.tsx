import { useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SaleLine } from "@/types/optimize";
import { numberToWords, parseIskInput } from "../utils/utils";

const SETTINGS_KEY = "manuoptimizer.haulOutSettings";
const MAX_TRIPS = 30; // more columns than this is unreadable (and a tiny max value could ask for millions)
const m3 = (v: number) => `${v.toLocaleString(undefined, { maximumFractionDigits: 1 })} m3`;
const isk = (v: number) => `${Math.round(v).toLocaleString()} ISK (${numberToWords(v)})`;

type Trip = { units: Record<string, number>; volume: number; value: number };

/**
 * Split the sales over `trips` loads so every load carries about the same share of
 * every item: same m3 and same ISK per trip. Leftover units go, one at a time, to the
 * load with the least m3 so far (then the least ISK).
 */
function splitEvenly(sales: SaleLine[], trips: number): Trip[] {
  const loads: Trip[] = Array.from({ length: trips }, () => ({ units: {}, volume: 0, value: 0 }));
  const ordered = [...sales].sort((a, b) => (b.unit_volume ?? 0) - (a.unit_volume ?? 0));
  for (const s of ordered) {
    const uv = s.unit_volume ?? 0;
    const unitValue = s.units > 0 ? s.value / s.units : 0;
    const base = Math.floor(s.units / trips);
    let rest = s.units - base * trips;
    for (const load of loads) {
      load.units[s.name] = base;
      load.volume += base * uv;
      load.value += base * unitValue;
    }
    while (rest > 0) {
      const target = loads.reduce((best, l) =>
        l.volume < best.volume - 1e-9 || (Math.abs(l.volume - best.volume) <= 1e-9 && l.value < best.value) ? l : best
      );
      target.units[s.name] += 1;
      target.volume += uv;
      target.value += unitValue;
      rest -= 1;
    }
  }
  return loads;
}

type HaulOutProps = {
  sales: SaleLine[];
  totalVolume: number;
  cargoPerTrip: number; // m3 per trip; 0 = not set
};

export default function HaulOut({ sales, totalVolume, cargoPerTrip }: HaulOutProps) {
  const [maxValueText, setMaxValueText] = useState("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(SETTINGS_KEY);
      if (raw) {
        const saved = JSON.parse(raw) as { maxValue?: string };
        if (typeof saved.maxValue === "string") setMaxValueText(saved.maxValue);
      }
    } catch {
      // defaults are fine
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (!loaded) return;
    try {
      window.localStorage.setItem(SETTINGS_KEY, JSON.stringify({ maxValue: maxValueText }));
    } catch {
      // harmless
    }
  }, [maxValueText, loaded]);

  const totalValue = sales.reduce((sum, s) => sum + s.value, 0);
  const unknownVolume = sales.filter((s) => s.volume_m3 === null || s.volume_m3 === undefined).map((s) => s.name);
  const maxValue = maxValueText.trim() === "" ? 0 : parseIskInput(maxValueText);
  const maxValueInvalid = maxValue === null;

  const plan = useMemo(() => {
    if (sales.length === 0) return null;
    const byVolume = cargoPerTrip > 0 ? Math.ceil(totalVolume / cargoPerTrip - 1e-9) : 1;
    const byValue = maxValue && maxValue > 0 ? Math.ceil(totalValue / maxValue - 1e-9) : 1;
    let trips = Math.max(1, byVolume, byValue);
    const capped = trips > MAX_TRIPS;
    trips = Math.min(trips, MAX_TRIPS);
    // Rounding units can push one load a little over capacity; add a trip until all fit.
    while (true) {
      const loads = splitEvenly(sales, trips);
      const over = cargoPerTrip > 0 && loads.some((l) => l.volume > cargoPerTrip + 1e-6);
      if (!over || trips >= MAX_TRIPS) return { trips, loads, byVolume, byValue, capped: capped || over };
      trips += 1;
    }
  }, [sales, totalVolume, totalValue, cargoPerTrip, maxValue]);

  if (!plan) return null;
  const names = [...sales].sort((a, b) => b.value - a.value).map((s) => s.name);

  return (
    <div className="rounded-2xl bg-gradient-to-br from-emerald-950 via-slate-900 to-slate-950 p-4 shadow-xl border border-emerald-800 w-full">
      <h3 className="text-xl text-emerald-300 font-semibold">Hauling Out</h3>
      <p className="text-sm text-emerald-100">
        Everything this plan sells: <strong>{m3(totalVolume)}</strong>, worth {isk(totalValue)} at the sell prices on record.
      </p>
      {cargoPerTrip > 0 && (
        <p className="text-sm text-emerald-100">
          {plan.byVolume} trip(s) of {m3(cargoPerTrip)} by volume.
        </p>
      )}
      {plan.capped && (
        <p className="text-xs text-yellow-300 mt-1">
          Your limits need {Math.max(plan.byVolume, plan.byValue).toLocaleString()} trips. The table shows {MAX_TRIPS},
          the most it splits into, so these loads are over your limits. Check the max value per trip
          (1.5b is 1,500,000,000; 15,000,000 is only 15 million).
        </p>
      )}
      {unknownVolume.length > 0 && (
        <p className="text-xs text-yellow-300 mt-1">Volume unknown, not counted: {unknownVolume.join(", ")}</p>
      )}

      <div className="flex flex-wrap items-end gap-4 mt-3">
        <div className="flex flex-col gap-1">
          <Label htmlFor="haulMaxValue" className="text-emerald-200">Max value per trip (ISK)</Label>
          <Input
            id="haulMaxValue"
            type="text"
            placeholder="empty = no limit"
            value={maxValueText}
            onChange={(e) => setMaxValueText(e.target.value)}
            aria-invalid={maxValueInvalid}
            className="bg-slate-900 border-emerald-800 text-emerald-100 placeholder:text-emerald-400/60 w-48"
          />
          <span className={`text-xs ${maxValueInvalid ? "text-red-400" : "text-emerald-400"}`}>
            {maxValueInvalid
              ? "Not a number. Examples: 500m, 1.2b, 1500000000"
              : maxValue && maxValue > 0
              ? `${Math.round(maxValue).toLocaleString()} ISK (${numberToWords(maxValue)}): ${plan.byValue} trip(s) by value`
              : "Splits into more, cheaper trips. Accepts 500m, 1.2b or a plain number"}
          </span>
        </div>
        <p className="text-xs text-emerald-300 max-w-md">
          Each trip carries the same share of every item, so no single load is the juicy one.
          Gankers pick targets by cargo value: keep each load well under what it costs them to kill you.
        </p>
      </div>

      <div className="overflow-auto mt-3">
        <table className="w-full text-sm text-left text-emerald-100 rounded-lg overflow-hidden border border-emerald-800">
          <thead className="bg-emerald-900 text-emerald-100">
            <tr>
              <th className="px-3 py-2">Item</th>
              {plan.loads.map((_, i) => (
                <th key={i} className="px-3 py-2 text-right">Trip {i + 1}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {names.map((name) => (
              <tr key={name} className="border-t border-emerald-900">
                <td className="px-3 py-1">{name}</td>
                {plan.loads.map((l, i) => (
                  <td key={i} className="px-3 py-1 text-right">{(l.units[name] ?? 0).toLocaleString()}</td>
                ))}
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-emerald-700 bg-emerald-900/40">
              <td className="px-3 py-1 font-semibold">Volume</td>
              {plan.loads.map((l, i) => (
                <td key={i} className="px-3 py-1 text-right">{m3(l.volume)}</td>
              ))}
            </tr>
            <tr className="bg-emerald-900/40">
              <td className="px-3 py-1 font-semibold">Value</td>
              {plan.loads.map((l, i) => (
                <td key={i} className="px-3 py-1 text-right">{Math.round(l.value).toLocaleString()}</td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
