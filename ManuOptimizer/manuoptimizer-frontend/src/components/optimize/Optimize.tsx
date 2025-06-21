'use client';

import React, { useState } from "react";
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




export default function Optimize() {
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleOptimize = async () => {
    setLoading(true);

    if (process.env.NODE_ENV === "development") {
      await waitForMswReady();
    }


    try {
      const res = await fetch("/api/blueprints/optimize");
      if (!res.ok) throw new Error("Failed to optimize");

      const data = await res.json();
      setResult(data);
      toast.success("Optimization complete!");
    } catch (err: any) {
      console.error("Optimization failed:", err);
      toast.error("Failed to optimize: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const optimizationData = result !== null ? {
    total_profit: result.total_profit,
    true_profit: result.true_profit,
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
        disabled={loading}
        className="bg-blue-900 hover:bg-blue-700 text-white font-bold text-lg py-4 px-6 rounded-lg shadow-lg shadow-blue-500/50 transition duration-300 ease-in-out hover:scale-110 hover:shadow-xl"
      >
        {loading ? "Optimizing..." : "OPTIMIZE PRODUCTION"}
      </Button>

        {result && (
          <div className="w-full space-y-6">
            {/* Totals */}
            {optimizationData && <OptimizationTotals data={optimizationData} />}

            {/* Grid layout for tables */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <DependenciesTable data={result.dependencies_needed} />
              <ProductionPlanTable data={result.what_to_produce} />
            </div>

            {/* Full width sections */}
            <MaterialUsageByCategory usage={result.material_usage} />
            <BottleneckList materialUsage={result.material_usage} />
          </div>
        )}

      </CardContent>
    </Card>
  );
}
