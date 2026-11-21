import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BuyListCandidate, BuyListSaveResponse } from "@/types/optimize";

// Ticked (but not saved) when the saved list is empty, so one Save sets it up.
const STARTER_LIST = ["Nocxium", "Tritanium", "Morphite"];

type BuyListPanelProps = {
  className?: string;
  onSaved?: (names: string[]) => void;
};

export default function BuyListPanel({ className, onSaved }: BuyListPanelProps) {
  const [open, setOpen] = useState(false);
  const [candidates, setCandidates] = useState<BuyListCandidate[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [saved, setSaved] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/buylist/candidates");
      if (!res.ok) throw new Error("Failed to load the buy list");
      const data: BuyListCandidate[] = await res.json();
      setCandidates(data);
      const onList = new Set(data.filter((c) => c.on_list).map((c) => c.name));
      setSaved(onList);
      if (onList.size === 0) {
        const known = new Set(data.map((c) => c.name));
        setSelected(new Set(STARTER_LIST.filter((n) => known.has(n))));
      } else {
        setSelected(new Set(onList));
      }
    } catch (err) {
      console.error(err);
      toast.error("Could not load the buy list");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const dirty = useMemo(() => {
    if (selected.size !== saved.size) return true;
    for (const n of selected) if (!saved.has(n)) return true;
    return false;
  }, [selected, saved]);

  const grouped = useMemo(() => {
    const q = filter.trim().toLowerCase();
    const groups = new Map<string, BuyListCandidate[]>();
    for (const c of candidates) {
      if (q && !c.name.toLowerCase().includes(q)) continue;
      const list = groups.get(c.category) ?? [];
      list.push(c);
      groups.set(c.category, list);
    }
    return Array.from(groups.entries());
  }, [candidates, filter]);

  const toggle = (name: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const save = async () => {
    setSaving(true);
    try {
      const res = await fetch("/api/buylist", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ names: Array.from(selected) }),
      });
      if (!res.ok) throw new Error("Failed to save the buy list");
      const data: BuyListSaveResponse = await res.json();
      if (data.unknown.length) toast.warning(`Not found in the SDE, not added: ${data.unknown.join(", ")}`);
      if (data.no_price.length) toast.warning(`No market price yet for: ${data.no_price.join(", ")}`);
      toast.success("Buy list saved");
      await load();
      onSaved?.(data.items.map((i) => i.name));
    } catch (err) {
      console.error(err);
      toast.error("Could not save the buy list");
    } finally {
      setSaving(false);
    }
  };

  const summary = saved.size === 0 ? "empty" : Array.from(saved).sort().join(", ");

  return (
    <div className={`w-full rounded-2xl bg-slate-900/60 border border-blue-800 p-4 ${className ?? ""}`}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between text-left"
        aria-expanded={open}
      >
        <span className="text-blue-200 font-semibold">
          Buy list <span className="text-blue-400 font-normal">({summary})</span>
        </span>
        <span className="text-blue-400 text-sm">{open ? "Hide" : "Edit"}</span>
      </button>

      {open && (
        <div className="mt-3 space-y-3">
          <p className="text-xs text-blue-400">
            With a budget and &quot;My buy list&quot;, the shopping list only contains what is ticked here.
            Items you hold none of can still be bought.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              type="text"
              placeholder="Filter materials"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-slate-900 border-blue-800 text-blue-100 placeholder:text-blue-400/60 max-w-xs"
            />
            <Button
              onClick={save}
              disabled={saving || !dirty}
              className="bg-blue-900 hover:bg-blue-700 text-white"
            >
              {saving ? "Saving..." : dirty ? "Save buy list" : "Saved"}
            </Button>
            {dirty && <span className="text-xs text-yellow-300">Unsaved changes</span>}
          </div>

          {loading ? (
            <p className="text-blue-300 text-sm">Loading...</p>
          ) : candidates.length === 0 ? (
            <p className="text-blue-300 text-sm">No blueprint inputs found. Add blueprints first.</p>
          ) : (
            <div className="max-h-80 overflow-y-auto space-y-3 pr-1">
              {grouped.map(([category, items]) => (
                <div key={category}>
                  <h4 className="text-sm text-blue-300 font-semibold mb-1">{category}</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1">
                    {items.map((c) => (
                      <label
                        key={c.name}
                        className="flex items-center gap-2 rounded px-2 py-1 text-sm text-blue-100 hover:bg-slate-800 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selected.has(c.name)}
                          onChange={() => toggle(c.name)}
                          className="accent-blue-500"
                        />
                        <span className="flex-1 truncate" title={c.name}>{c.name}</span>
                        <span className="text-xs text-blue-400 whitespace-nowrap">
                          {c.sell_price ? `${c.sell_price.toLocaleString()} ISK` : "no price"}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
