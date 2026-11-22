import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SuggestedMaxResponse, SuggestedMaxRow } from "@/types/blueprints";

const SETTINGS_KEY = "manuoptimizer.suggestedMaxSettings";

type SuggestedMaxPanelProps = {
  onApplied?: () => void;
};

export default function SuggestedMaxPanel({ onApplied }: SuggestedMaxPanelProps) {
  const [open, setOpen] = useState(false);
  const [daysText, setDaysText] = useState("3");
  const [windowText, setWindowText] = useState("30");
  const [rows, setRows] = useState<SuggestedMaxRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(SETTINGS_KEY);
      if (raw) {
        const saved = JSON.parse(raw) as { days?: string; window?: string };
        if (typeof saved.days === "string") setDaysText(saved.days);
        if (typeof saved.window === "string") setWindowText(saved.window);
      }
    } catch {
      // Storage unavailable; defaults are fine.
    }
    setSettingsLoaded(true);
  }, []);

  useEffect(() => {
    if (!settingsLoaded) return;
    try {
      window.localStorage.setItem(SETTINGS_KEY, JSON.stringify({ days: daysText, window: windowText }));
    } catch {
      // Harmless.
    }
  }, [daysText, windowText, settingsLoaded]);

  const days = Number(daysText);
  const windowDays = Number(windowText);
  const daysInvalid = !Number.isFinite(days) || days < 0;
  const windowInvalid = !Number.isInteger(windowDays) || windowDays < 1 || windowDays > 365;

  const load = async () => {
    if (daysInvalid || windowInvalid) {
      toast.error("Days must be 0 or more; history window between 1 and 365");
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams({ days: String(days), window: String(windowDays) });
      const res = await fetch(`/api/blueprints/blueprints/suggested_max?${params}`);
      if (!res.ok) throw new Error("Failed to load market volumes");
      const data: SuggestedMaxResponse = await res.json();
      setRows(data.blueprints);
    } catch (err) {
      console.error(err);
      toast.error("Could not load market volumes from ESI");
    } finally {
      setLoading(false);
    }
  };

  const apply = async (targets: SuggestedMaxRow[]) => {
    const values: Record<string, number> = {};
    for (const r of targets) {
      if (r.suggested_max !== null) values[String(r.id)] = r.suggested_max;
    }
    if (Object.keys(values).length === 0) {
      toast.info("Nothing to apply");
      return;
    }
    setApplying(true);
    try {
      const res = await fetch("/api/blueprints/blueprints/set_max", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max: values }),
      });
      if (!res.ok) throw new Error("Failed to set max");
      const data = await res.json();
      toast.success(data.message ?? "Max updated");
      setRows((prev) =>
        prev.map((r) => (values[String(r.id)] !== undefined ? { ...r, current_max: values[String(r.id)] } : r))
      );
      onApplied?.();
    } catch (err) {
      console.error(err);
      toast.error("Could not apply the suggested max");
    } finally {
      setApplying(false);
    }
  };

  const withoutMax = rows.filter((r) => r.current_max === null && r.suggested_max !== null);
  const changed = rows.filter((r) => r.suggested_max !== null && r.suggested_max !== r.current_max);
  const inputClass = "bg-slate-900 border-blue-800 text-blue-100 placeholder:text-blue-400/60";

  return (
    <div className="mx-6 mt-4 rounded-2xl bg-slate-900/60 border border-blue-800 p-4">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between text-left"
        aria-expanded={open}
      >
        <span className="text-blue-200 font-semibold">Suggested max from market volume</span>
        <span className="text-blue-400 text-sm">{open ? "Hide" : "Show"}</span>
      </button>

      {open && (
        <div className="mt-3 space-y-3">
          <p className="text-xs text-blue-400">
            Max = days of sales x average units traded per day (ESI market history, the blueprint&apos;s region).
            The optimizer never plans to sell more than max.
          </p>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1">
              <Label htmlFor="suggestDays" className="text-blue-200">Days of sales</Label>
              <Input id="suggestDays" type="number" min={0} step={0.5} value={daysText}
                onChange={(e) => setDaysText(e.target.value)} aria-invalid={daysInvalid}
                className={`${inputClass} w-28`} />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="suggestWindow" className="text-blue-200">Average over (days)</Label>
              <Input id="suggestWindow" type="number" min={1} max={365} step={1} value={windowText}
                onChange={(e) => setWindowText(e.target.value)} aria-invalid={windowInvalid}
                className={`${inputClass} w-28`} />
            </div>
            <Button onClick={load} disabled={loading} className="bg-blue-900 hover:bg-blue-700 text-white">
              {loading ? "Loading volumes..." : rows.length ? "Recalculate" : "Get suggestions"}
            </Button>
            {rows.length > 0 && (
              <>
                <Button onClick={() => apply(withoutMax)} disabled={applying || withoutMax.length === 0}
                  className="bg-blue-800 hover:bg-blue-700 text-white">
                  Apply where no max ({withoutMax.length})
                </Button>
                <Button onClick={() => apply(changed)} disabled={applying || changed.length === 0}
                  className="bg-blue-800 hover:bg-blue-700 text-white">
                  Apply all ({changed.length})
                </Button>
              </>
            )}
          </div>

          {rows.length > 0 && (
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-sm text-blue-100">
                <thead className="sticky top-0 bg-slate-900 text-blue-300">
                  <tr>
                    <th className="text-left py-1 px-2">Blueprint</th>
                    <th className="text-right py-1 px-2">Avg / day</th>
                    <th className="text-right py-1 px-2">Current max</th>
                    <th className="text-right py-1 px-2">Suggested</th>
                    <th className="py-1 px-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id} className="border-t border-blue-900/60">
                      <td className="py-1 px-2">{r.name}</td>
                      <td className="py-1 px-2 text-right">
                        {r.avg_daily_volume === null ? "no data" : r.avg_daily_volume.toLocaleString()}
                      </td>
                      <td className="py-1 px-2 text-right">{r.current_max ?? "none"}</td>
                      <td className="py-1 px-2 text-right font-semibold">
                        {r.suggested_max === null ? "-" : r.suggested_max.toLocaleString()}
                      </td>
                      <td className="py-1 px-2 text-right">
                        <Button size="sm" onClick={() => apply([r])}
                          disabled={applying || r.suggested_max === null || r.suggested_max === r.current_max}
                          className="h-7 bg-blue-900 hover:bg-blue-700 text-white">
                          Apply
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
