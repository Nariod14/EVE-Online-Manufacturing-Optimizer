import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ItemSearchResult, Material } from "@/types/materials";

const MINERALS = ["Tritanium", "Pyerite", "Mexallon", "Isogen", "Nocxium", "Zydrine", "Megacyte", "Morphite"];

/** Whole number >= 0 from "5000", "5,000", "5 000" or "5.000"; null if it is not one. */
export function parseQuantity(text: string): number | null {
  let t = text.replace(/[\s,'  ]/g, "");
  if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, "");
  if (!/^\d+$/.test(t)) return null;
  const n = Number(t);
  return Number.isSafeInteger(n) ? n : null;
}

async function errorMessage(res: Response, fallback: string) {
  const body = await res.json().catch(() => null);
  return body?.error || body?.ERROR || fallback;
}

type AddItemPanelProps = {
  materials: Material[];
  onChanged: () => void | Promise<void>;
};

export default function AddItemPanel({ materials, onChanged }: AddItemPanelProps) {
  // ---- search and add one item
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ItemSearchResult[]>([]);
  const [highlight, setHighlight] = useState(0);
  const [picked, setPicked] = useState<ItemSearchResult | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [qtyText, setQtyText] = useState("");
  const [mode, setMode] = useState<"set" | "add">("set");
  const [saving, setSaving] = useState(false);
  const requestSeq = useRef(0);
  const qtyRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const q = query.trim();
    if (picked || q.length < 2) {
      setResults([]);
      return;
    }
    const seq = ++requestSeq.current;
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/materials/search?q=${encodeURIComponent(q)}`);
        if (!res.ok) throw new Error(await errorMessage(res, "Search failed"));
        const data: ItemSearchResult[] = await res.json();
        if (seq === requestSeq.current) {   // ignore answers to older keystrokes
          setResults(data);
          setHighlight(0);
          setShowResults(true);
        }
      } catch (err) {
        console.error(err);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [query, picked]);

  const owned = useMemo(() => new Map(materials.map((m) => [m.name, m])), [materials]);

  const pick = (item: ItemSearchResult) => {
    setPicked(item);
    setQuery(item.name);
    setShowResults(false);
    setResults([]);
    setTimeout(() => qtyRef.current?.focus(), 0);
  };

  const qty = parseQuantity(qtyText);
  const current = picked ? owned.get(picked.name) : undefined;

  const addItem = async () => {
    if (!picked) {
      toast.error("Pick an item from the list first");
      return;
    }
    if (qty === null) {
      toast.error("Quantity must be a whole number, 0 or more");
      return;
    }
    setSaving(true);
    try {
      const res = await fetch("/api/materials/materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: picked.name, quantity: qty, mode }),
      });
      if (!res.ok) throw new Error(await errorMessage(res, "Could not add the item"));
      const data = await res.json();
      toast.success(`${data.created ? "Added" : "Updated"} ${data.message}`);
      setPicked(null);
      setQuery("");
      setQtyText("");
      await onChanged();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not add the item");
    } finally {
      setSaving(false);
    }
  };

  const onSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showResults || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      pick(results[highlight]);
    } else if (e.key === "Escape") {
      setShowResults(false);
    }
  };

  // ---- minerals quick edit
  const [mineralText, setMineralText] = useState<Record<string, string>>({});
  const [savingMinerals, setSavingMinerals] = useState(false);

  useEffect(() => {
    const next: Record<string, string> = {};
    for (const name of MINERALS) {
      const m = owned.get(name);
      next[name] = m ? String(m.quantity) : "";
    }
    setMineralText(next);
  }, [owned]);

  const mineralChanges = MINERALS.filter((name) => {
    const text = (mineralText[name] ?? "").trim();
    const have = owned.get(name);
    if (text === "") return false;                      // blank = leave alone
    const n = parseQuantity(text);
    return n === null || !have || have.quantity !== n;
  });
  const mineralErrors = mineralChanges.filter((name) => parseQuantity(mineralText[name] ?? "") === null);

  const saveMinerals = async () => {
    if (mineralErrors.length) {
      toast.error(`Not a whole number: ${mineralErrors.join(", ")}`);
      return;
    }
    setSavingMinerals(true);
    const failed: string[] = [];
    for (const name of mineralChanges) {
      const res = await fetch("/api/materials/materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, quantity: parseQuantity(mineralText[name]), mode: "set" }),
      }).catch(() => null);
      if (!res || !res.ok) failed.push(name);
    }
    setSavingMinerals(false);
    if (failed.length) toast.error(`Could not save: ${failed.join(", ")}`);
    else toast.success(`Saved ${mineralChanges.length} mineral(s)`);
    await onChanged();
  };

  // ---- add every blueprint input at 0
  const [addingInputs, setAddingInputs] = useState(false);
  const addMissingInputs = async () => {
    setAddingInputs(true);
    try {
      const res = await fetch("/api/materials/add_missing_inputs", { method: "POST" });
      if (!res.ok) throw new Error(await errorMessage(res, "Could not add the inputs"));
      const data: { added: string[]; unknown: string[] } = await res.json();
      if (data.added.length) toast.success(`Added at 0: ${data.added.join(", ")}`);
      else toast.info("Every blueprint input is already in your materials");
      if (data.unknown.length) toast.warning(`Not found in the SDE: ${data.unknown.join(", ")}`);
      await onChanged();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not add the inputs");
    } finally {
      setAddingInputs(false);
    }
  };

  const inputClass = "bg-slate-900 border-blue-800 text-blue-100 placeholder:text-blue-400/60";

  return (
    <div className="rounded-xl bg-slate-900/60 border border-blue-800 p-4 space-y-4">
      {/* Search and add */}
      <div className="space-y-2">
        <h3 className="text-blue-200 font-semibold">Add an item</h3>
        <div className="flex flex-wrap items-end gap-2">
          <div className="relative flex-1 min-w-[220px]">
            <Label htmlFor="itemSearch" className="text-blue-300 text-xs">Item (type 2+ letters)</Label>
            <Input
              id="itemSearch"
              role="combobox"
              aria-expanded={showResults && results.length > 0}
              aria-controls="itemSearchResults"
              autoComplete="off"
              placeholder="e.g. Morphite"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPicked(null);
              }}
              onKeyDown={onSearchKey}
              onFocus={() => results.length && setShowResults(true)}
              onBlur={() => setTimeout(() => setShowResults(false), 150)}
              className={inputClass}
            />
            {showResults && results.length > 0 && (
              <ul
                id="itemSearchResults"
                role="listbox"
                className="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-md border border-blue-800 bg-slate-950 shadow-xl"
              >
                {results.map((r, i) => (
                  <li
                    key={r.type_id}
                    role="option"
                    aria-selected={i === highlight}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      pick(r);
                    }}
                    onMouseEnter={() => setHighlight(i)}
                    className={`flex justify-between gap-2 px-3 py-1.5 text-sm cursor-pointer ${
                      i === highlight ? "bg-blue-900 text-white" : "text-blue-100"
                    }`}
                  >
                    <span>{r.name}</span>
                    <span className="text-xs text-blue-400">
                      {owned.has(r.name) ? `have ${owned.get(r.name)!.quantity.toLocaleString()}` : r.category}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {showResults && query.trim().length >= 2 && !picked && results.length === 0 && (
              <p className="absolute mt-1 text-xs text-yellow-300">No item matches</p>
            )}
          </div>

          <div className="w-36">
            <Label htmlFor="itemQty" className="text-blue-300 text-xs">Quantity</Label>
            <Input
              id="itemQty"
              ref={qtyRef}
              inputMode="numeric"
              placeholder="0"
              value={qtyText}
              onChange={(e) => setQtyText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addItem()}
              aria-invalid={qtyText.trim() !== "" && qty === null}
              className={inputClass}
            />
          </div>

          <div>
            <Label htmlFor="itemMode" className="text-blue-300 text-xs">If you have some</Label>
            <select
              id="itemMode"
              value={mode}
              onChange={(e) => setMode(e.target.value as "set" | "add")}
              className="h-9 rounded-md border border-blue-800 bg-slate-900 px-2 text-sm text-blue-100 block"
            >
              <option value="set">Set to this</option>
              <option value="add">Add to it</option>
            </select>
          </div>

          <Button onClick={addItem} disabled={saving || !picked || qty === null} className="bg-blue-700 hover:bg-blue-800 text-white">
            {saving ? "Saving..." : "Add"}
          </Button>
        </div>
        {picked && (
          <p className="text-xs text-blue-400">
            {picked.name} ({picked.category}){current ? `: you have ${current.quantity.toLocaleString()}` : ": not in your materials yet"}
            {current && qty !== null && ` -> ${(mode === "add" ? current.quantity + qty : qty).toLocaleString()}`}
          </p>
        )}
      </div>

      {/* Minerals */}
      <div className="space-y-2">
        <h3 className="text-blue-200 font-semibold">Minerals</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {MINERALS.map((name) => {
            const text = mineralText[name] ?? "";
            const invalid = text.trim() !== "" && parseQuantity(text) === null;
            return (
              <div key={name}>
                <Label htmlFor={`min-${name}`} className="text-blue-300 text-xs">{name}</Label>
                <Input
                  id={`min-${name}`}
                  inputMode="numeric"
                  placeholder="not tracked"
                  value={text}
                  onChange={(e) => setMineralText((prev) => ({ ...prev, [name]: e.target.value }))}
                  aria-invalid={invalid}
                  className={inputClass}
                />
              </div>
            );
          })}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={saveMinerals} disabled={savingMinerals || mineralChanges.length === 0}
            className="bg-blue-700 hover:bg-blue-800 text-white">
            {savingMinerals ? "Saving..." : `Save minerals${mineralChanges.length ? ` (${mineralChanges.length})` : ""}`}
          </Button>
          <Button onClick={addMissingInputs} disabled={addingInputs} variant="secondary"
            className="bg-slate-700 text-blue-200 hover:bg-slate-600">
            {addingInputs ? "Adding..." : "Add missing blueprint inputs at 0"}
          </Button>
        </div>
      </div>
    </div>
  );
}
