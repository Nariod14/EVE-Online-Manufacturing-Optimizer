'use client';

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import OptimizationTotals from "./OptimizationTotals";
import DependenciesTable from "./DependenciesTable";
import ProductionPlanTable from "./ProductionPlanTable";
import MaterialUsageByCategory from "./MaterialUsageByCategory";
import BottleneckList from "./BottleneckList";
import ShoppingList from "./ShoppingList";
import RestockPriority from "./RestockPriority";
import BuyListPanel from "./BuyListPanel";
import HaulOut from "./HaulOut";
import { BuyMode, OptimizeResponse } from "@/types/optimize";
import AdjustedProductionPlanTable from "./AdjustedProductionPlanTable";
import WhereToSell from "./WhereToSell";
import { fetchBlueprints } from "../blueprints/Blueprints";
import { Blueprint } from "@/types/blueprints";
import { fetchStations, Station } from "@/types/stations";
import { numberToWords, parseIskInput } from "../utils/utils";

const SETTINGS_KEY = "manuoptimizer.optimizeSettings";
const MAX_FEE_PERCENT = 50;

type StoredSettings = {
  budget?: string;
  fee?: string;
  buy?: BuyMode | "minerals"; // "minerals" was saved by older versions; it now means "list"
  cargo?: string;             // hauler capacity, m3 per trip
  trips?: string;
  limitBuy?: boolean;         // apply the cargo limit to what is bought
  limitSell?: boolean;        // ...and to what is sold
};

const DEFAULT_CARGO = "62500"; // DST, max skills
const DEFAULT_TRIPS = "2";

export default function Optimize() {
const [result, setResult] = useState<OptimizeResponse | null>(null);
const [loading, setLoading] = useState(false);
const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
const [stations, setStations] = useState<Station[]>([]);

// Optimizer settings. Empty budget / fee means "inventory only, no fees" (the old behaviour).
const [budgetText, setBudgetText] = useState("");
const [feeText, setFeeText] = useState("");
const [buyMode, setBuyMode] = useState<BuyMode>("list");
const [cargoText, setCargoText] = useState(DEFAULT_CARGO);
const [tripsText, setTripsText] = useState(DEFAULT_TRIPS);
const [limitBuy, setLimitBuy] = useState(true);
const [limitSell, setLimitSell] = useState(true);
const [settingsLoaded, setSettingsLoaded] = useState(false);

// Restore the last used settings
useEffect(() => {
  try {
    const raw = window.localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      const saved = JSON.parse(raw) as StoredSettings;
      if (typeof saved.budget === "string") setBudgetText(saved.budget);
      if (typeof saved.fee === "string") setFeeText(saved.fee);
      if (saved.buy === "minerals" || saved.buy === "list") setBuyMode("list");
      else if (saved.buy === "all" || saved.buy === "none") setBuyMode(saved.buy);
      if (typeof saved.cargo === "string") setCargoText(saved.cargo);
      if (typeof saved.trips === "string") setTripsText(saved.trips);
      if (typeof saved.limitBuy === "boolean") setLimitBuy(saved.limitBuy);
      if (typeof saved.limitSell === "boolean") setLimitSell(saved.limitSell);
    }
  } catch {
    // Storage can be unavailable (private window); the defaults are fine.
  }
  setSettingsLoaded(true);
}, []);

// Remember them for next time
useEffect(() => {
  if (!settingsLoaded) return;
  try {
    const toStore: StoredSettings = { budget: budgetText, fee: feeText, buy: buyMode, cargo: cargoText, trips: tripsText, limitBuy, limitSell };
    window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(toStore));
  } catch {
    // Not being able to save the settings is harmless.
  }
}, [budgetText, feeText, buyMode, cargoText, tripsText, limitBuy, limitSell, settingsLoaded]);

// Combined load on mount
useEffect(() => {
  const loadInitialData = async () => {
    const stationData = await fetchStations();
    setStations(stationData);

    await fetchBlueprints(setBlueprints, setLoading);

    // Map station names after both datasets are available
    const stationMap = new Map(stationData.map(s => [s.station_id, s.name]));
    setBlueprints(prev =>
      prev.map(bp => ({
        ...bp,
        station_name: bp.station_id ? stationMap.get(bp.station_id) ?? 'Jita 4-4 Caldari Navy Assembly Plant' : 'Jita 4-4 Caldari Navy Assembly Plant',
      }))
    );
  };

  loadInitialData();
}, []);

const budget = parseIskInput(budgetText);
const feePercent = feeText.trim() === "" ? 0 : Number(feeText);
const budgetInvalid = budget === null;
const feeInvalid = !Number.isFinite(feePercent) || feePercent < 0 || feePercent > MAX_FEE_PERCENT;
// Empty capacity = no cargo limit
const cargoPerTrip = cargoText.trim() === "" ? 0 : Number(cargoText.replace(/[\s,]/g, ""));
const trips = tripsText.trim() === "" ? 1 : Number(tripsText);
const cargoInvalid = !Number.isFinite(cargoPerTrip) || cargoPerTrip < 0;
const tripsInvalid = !Number.isInteger(trips) || trips < 1;
const cargoTotal = !cargoInvalid && !tripsInvalid ? cargoPerTrip * trips : 0;

const handleOptimize = async () => {
  if (budget === null) {
    toast.error("Buy budget is not a number. Examples: 200m, 1.5b, 250000000");
    return;
  }
  if (feeInvalid) {
    toast.error(`Fees must be a percentage between 0 and ${MAX_FEE_PERCENT}`);
    return;
  }
  if (cargoInvalid || tripsInvalid) {
    toast.error("Cargo must be a number of m3 (or empty for no limit) and trips a whole number of 1 or more");
    return;
  }

  setLoading(true);

  try {
    const params = new URLSearchParams();
    if (budget > 0 && buyMode !== "none") {
      params.set("budget", String(Math.round(budget)));
      params.set("buy", buyMode);
    }
    if (cargoTotal > 0 && (limitBuy || limitSell)) {
      params.set("cargo", String(cargoTotal));
      if (!limitBuy) params.set("cargo_buy", "0");
      if (!limitSell) params.set("cargo_sell", "0");
    }
    if (feePercent > 0) {
      // The backend takes the fee as a fraction: 5% is sent as 0.05
      params.set("fee", String(feePercent / 100));
    }
    const query = params.toString();

    const res = await fetch("/api/blueprints/optimize" + (query ? `?${query}` : ""));
    if (!res.ok) {
      const problem = await res.json().catch(() => null);
      throw new Error(problem?.status || problem?.error || "Failed to optimize");
    }

    const data = await res.json();
    setResult(data);

    // Refresh blueprints after optimization
    await fetchBlueprints(setBlueprints, setLoading);

    const stationMap = new Map(stations.map(s => [s.station_id, s.name]));
    setBlueprints(prev =>
      prev.map(bp => ({
        ...bp,
        station_name: bp.station_id ? stationMap.get(bp.station_id) ?? 'Jita 4-4 Caldari Navy Assembly Plant' : 'Jita 4-4 Caldari Navy Assembly Plant',
      }))
    );

    toast.success("Optimization complete!");
  } catch (err) {
    console.error("Optimization failed:", err);
    toast.error(err instanceof Error && err.message ? err.message : "Failed to optimize");
  } finally {
    setLoading(false);
  }
};

const optimizationData = result !== null ? {
  total_profit: result.total_profit,
  true_profit_jita: result.true_profit_jita,
  true_profit_inventory: result.true_profit_inventory,
  inventory_savings: result.inventory_savings,
  expected_invention_materials_used: result.expected_invention_materials_used,
  invention_cost: result.invention_cost,
  sales_fees: result.sales_fees,
  purchase_cost: result.purchase_cost,
  cash_profit: result.cash_profit,
  original_final_produced: result.original_production_plan,
  adjusted_final_produced: result.adjusted_production_plan,
} : null;

const inputClass = "bg-slate-900 border-blue-800 text-blue-100 placeholder:text-blue-400/60";
const willBuy = budget !== null && budget > 0 && buyMode !== "none";

  return (
    <Card className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-2xl w-full p-6">
      <CardHeader>
        <CardTitle className="text-2xl text-blue-100 mb-2">
          Optimize Production
        </CardTitle>
      </CardHeader>

      <CardContent className="flex flex-col items-center space-y-6">
        {/* Settings */}
        <div className="w-full rounded-2xl bg-slate-900/60 border border-blue-800 p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col gap-1">
              <Label htmlFor="optimizeBudget" className="text-blue-200">Buy budget (ISK)</Label>
              <Input
                id="optimizeBudget"
                type="text"
                inputMode="decimal"
                placeholder="0 = use inventory only"
                value={budgetText}
                onChange={(e) => setBudgetText(e.target.value)}
                aria-invalid={budgetInvalid}
                className={inputClass}
              />
              <span className={`text-xs ${budgetInvalid ? "text-red-400" : "text-blue-400"}`}>
                {budgetInvalid
                  ? "Not a number. Examples: 200m, 1.5b, 250000000"
                  : budget && budget > 0
                  ? `${Math.round(budget).toLocaleString()} ISK (${numberToWords(budget)})`
                  : "Accepts 200m, 1.5b or a plain number"}
              </span>
            </div>

            <div className="flex flex-col gap-1">
              <Label htmlFor="optimizeBuyMode" className="text-blue-200">Spend it on</Label>
              <select
                id="optimizeBuyMode"
                value={buyMode}
                onChange={(e) => setBuyMode(e.target.value as BuyMode)}
                className="h-9 rounded-md border border-blue-800 bg-slate-900 px-3 text-sm text-blue-100"
              >
                <option value="list">My buy list</option>
                <option value="all">Anything with a price</option>
                <option value="none">Nothing (inventory only)</option>
              </select>
              <span className={`text-xs ${willBuy && buyMode === "all" ? "text-yellow-300" : "text-blue-400"}`}>
                {!willBuy
                  ? "Nothing is bought; only your inventory is used."
                  : buyMode === "all"
                  ? "Buys anything with a price. Your buy list is ignored in this mode."
                  : "Only items on your buy list are bought."}
              </span>
            </div>

            <div className="flex flex-col gap-1">
              <Label htmlFor="optimizeFee" className="text-blue-200">Sales tax + broker fee (%)</Label>
              <Input
                id="optimizeFee"
                type="number"
                min={0}
                max={MAX_FEE_PERCENT}
                step={0.1}
                placeholder="0"
                value={feeText}
                onChange={(e) => setFeeText(e.target.value)}
                aria-invalid={feeInvalid}
                className={inputClass}
              />
              <span className={`text-xs ${feeInvalid ? "text-red-400" : "text-blue-400"}`}>
                {feeInvalid ? `Enter a percentage between 0 and ${MAX_FEE_PERCENT}` : "Taken off the sell value of everything sold"}
              </span>
            </div>

            <div className="flex flex-col gap-1">
              <Label htmlFor="optimizeCargo" className="text-blue-200">Hauler capacity (m3 per trip)</Label>
              <Input
                id="optimizeCargo"
                type="text"
                inputMode="decimal"
                placeholder="empty = no limit"
                value={cargoText}
                onChange={(e) => setCargoText(e.target.value)}
                aria-invalid={cargoInvalid}
                className={inputClass}
              />
              <span className={`text-xs ${cargoInvalid ? "text-red-400" : "text-blue-400"}`}>
                {cargoInvalid ? "Not a number of m3" : "62,500 = DST at max skills"}
              </span>
            </div>

            <div className="flex flex-col gap-1">
              <Label htmlFor="optimizeTrips" className="text-blue-200">Trips</Label>
              <Input
                id="optimizeTrips"
                type="number"
                min={1}
                step={1}
                value={tripsText}
                onChange={(e) => setTripsText(e.target.value)}
                aria-invalid={tripsInvalid}
                className={inputClass}
              />
              <span className={`text-xs ${tripsInvalid ? "text-red-400" : "text-blue-400"}`}>
                {tripsInvalid
                  ? "A whole number, 1 or more"
                  : cargoTotal > 0 && (limitBuy || limitSell)
                  ? `${limitBuy && limitSell ? "What you buy and what you sell must each" : limitBuy ? "What you buy must" : "What you sell must"} fit in ${cargoTotal.toLocaleString()} m3`
                  : "No cargo limit"}
              </span>
            </div>

            <div className="flex flex-col gap-2">
              <span className="text-blue-200 text-sm font-medium">Apply the cargo limit to</span>
              <label className="flex items-center gap-2 text-sm text-blue-100 cursor-pointer">
                <input type="checkbox" checked={limitBuy} onChange={(e) => setLimitBuy(e.target.checked)} className="accent-blue-500" />
                What I buy (trips in)
              </label>
              <label className="flex items-center gap-2 text-sm text-blue-100 cursor-pointer">
                <input type="checkbox" checked={limitSell} onChange={(e) => setLimitSell(e.target.checked)} className="accent-blue-500" />
                What I sell (trips out)
              </label>
              <span className="text-xs text-blue-400">Untick one and optimize again to see what the limit costs you</span>
            </div>
          </div>
        </div>

        <BuyListPanel />

        <Button
          onClick={handleOptimize}
          disabled={loading || blueprints.length === 0}
          className="bg-blue-900 hover:bg-blue-700 text-white font-bold text-lg py-4 px-6 rounded-lg shadow-lg shadow-blue-500/50 transition duration-300 ease-in-out hover:scale-110 hover:shadow-xl"
        >
          {loading ? "Optimizing..." : "OPTIMIZE PRODUCTION"}
        </Button>

        {result && (
          <div className="w-full space-y-6">
            {/* Things the optimizer could not price or build */}
            {result.warnings && result.warnings.length > 0 && (
              <div className="rounded-2xl border border-yellow-700 bg-yellow-950/40 p-4 text-sm text-yellow-100">
                <h3 className="text-lg font-semibold text-yellow-300 mb-1">Check these before trusting the plan</h3>
                <ul className="list-disc pl-5 space-y-1">
                  {result.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Totals */}
            {optimizationData && <OptimizationTotals data={optimizationData} />}

            {/* Tables container */}
            {(Object.keys(result.dependencies_needed || {}).length > 0 ||
              Object.keys(result.what_to_produce || {}).length > 0 ||
              Object.keys(result.adjusted_production_plan || {}).length > 0) && (
              <div className="w-full">
                {/* Calculate how many tables we have */}
                {(() => {
                  const tableCount = [
                    result.dependencies_needed,
                    result.what_to_produce,
                    result.adjusted_production_plan,
                  ].filter(data => data && Object.keys(data).length > 0).length;

                  return (
                    <div className={`grid grid-cols-1 ${tableCount === 2 ? 'md:grid-cols-2' : tableCount === 3 ? 'md:grid-cols-3' : 'md:grid-cols-1'} gap-3 items-stretch`}>
                      {Object.keys(result.dependencies_needed || {}).length > 0 && (
                        <div className={`h-full ${tableCount === 1 ? 'md:col-span-1 mx-auto w-full md:w-2/5' : 'w-full'}`}>
                          <DependenciesTable data={result.dependencies_needed} className="h-full" />
                        </div>
                      )}

                      {Object.keys(result.what_to_produce || {}).length > 0 && (
                        <div className={`h-full ${tableCount === 1 ? 'md:col-span-1 mx-auto w-full md:w-2/5' : 'w-full'}`}>
                          <ProductionPlanTable data={result.what_to_produce} plan={result.production_plan} className="h-full" />
                        </div>
                      )}

                      {Object.keys(result.adjusted_production_plan || {}).length > 0 && (
                        <div className={`h-full ${tableCount === 1 ? 'md:col-span-1 mx-auto w-full md:w-2/5' : 'w-full'}`}>
                          <AdjustedProductionPlanTable data={result.adjusted_production_plan} className="h-full" />
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}

            {/* What to buy, when a budget was given */}
            {result.shopping_list && Object.keys(result.shopping_list).length > 0 && (
              <ShoppingList items={result.shopping_list} total={result.purchase_cost ?? 0} buyMode={result.settings?.buy}
                totalVolume={result.purchase_volume} cargoPerTrip={cargoInvalid ? 0 : cargoPerTrip} />
            )}

            {/* Volume of what gets sold, and how to split it over trips */}
            {result.sales && result.sales.length > 0 && (
              <HaulOut
                sales={result.sales}
                totalVolume={result.sell_volume ?? 0}
                cargoPerTrip={cargoInvalid ? 0 : cargoPerTrip}
              />
            )}

            {/* Which materials are holding the plan back */}
            {result.marginal_values && result.marginal_values.length > 0 && (
              <RestockPriority items={result.marginal_values} />
            )}

            {/* Where to sell */}
            {result.adjusted_production_plan && (
              blueprints.length > 0 ? (
                <WhereToSell 
                  productionPlan={result.adjusted_production_plan}
                  allBlueprints={blueprints}
                />
              ) : (
                <p className="text-blue-300">Loading blueprints...</p>
              )
            )}


            {/* Full width sections */}
            <MaterialUsageByCategory
              usage={result.material_usage}
              savings={result.inventory_savings}
              expected_invention={result.expected_invention_materials_used}
              invention_cost={result.invention_cost}
            />

            <BottleneckList materialUsage={result.material_usage} />
          </div>
        )}


      </CardContent>
    </Card>
  );



}
