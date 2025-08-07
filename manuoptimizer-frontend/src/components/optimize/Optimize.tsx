'use client';

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import toast from "react-hot-toast";
import OptimizationTotals from "./OptimizationTotals";
import DependenciesTable from "./DependenciesTable";
import ProductionPlanTable from "./ProductionPlanTable";
import MaterialUsageByCategory from "./MaterialUsageByCategory";
import BottleneckList from "./BottleneckList";
import { OptimizeResponse } from "@/types/optimize";
import { waitForMswReady } from "@/lib/mswReady";
import AdjustedProductionPlanTable from "./AdjustedProductionPlanTable";
import WhereToSell from "./WhereToSell";
import { fetchBlueprints } from "../blueprints/Blueprints";
import { Blueprint } from "@/types/blueprints";
import { fetchStations, Station } from "@/types/stations";




export default function Optimize() {
const [result, setResult] = useState<OptimizeResponse | null>(null);
const [loading, setLoading] = useState(false);
const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
const [stations, setStations] = useState<Station[]>([]);

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

const handleOptimize = async () => {
  setLoading(true);

  try {
    const res = await fetch("/api/blueprints/optimize");
    if (!res.ok) throw new Error("Failed to optimize");

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
    toast.error("Failed to optimize");
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
  original_final_produced: result.original_production_plan,
  adjusted_final_produced: result.adjusted_production_plan,
} : null;
  

  return (
    <Card className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-2xl w-full p-6">
      <CardHeader>
        <CardTitle className="text-2xl text-blue-100 mb-2">
          Optimize Production
        </CardTitle>
      </CardHeader>

      <CardContent className="flex flex-col items-center space-y-6">
        <Button
          onClick={handleOptimize}
          disabled={loading || blueprints.length === 0}
          className="bg-blue-900 hover:bg-blue-700 text-white font-bold text-lg py-4 px-6 rounded-lg shadow-lg shadow-blue-500/50 transition duration-300 ease-in-out hover:scale-110 hover:shadow-xl"
        >
          {loading ? "Optimizing..." : "OPTIMIZE PRODUCTION"}
        </Button>

        {result && (
          <div className="w-full space-y-6">
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
                          <ProductionPlanTable data={result.what_to_produce} className="h-full" />
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
