"use client";

import { SetStateAction, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner"; // or your preferred toast library

type BlueprintTier = "T1" | "T2";

type BlueprintParserProps = {
  stations?: { id: number; name: string }[]; // For station dropdown
};

export default function BlueprintParser({ stations = [] }: BlueprintParserProps) {
  // State for From Game parser
  const [tier, setTier] = useState<BlueprintTier>("T1");
  const [sellPrice, setSellPrice] = useState("");
  const [makeCost, setMakeCost] = useState("");
  const [blueprintData, setBlueprintData] = useState("");
  const [inventionData, setInventionData] = useState("");
  const [inventionChance, setInventionChance] = useState("");
  const [runsPerCopy, setRunsPerCopy] = useState("10");
  const [stationId, setStationId] = useState("");
  const [loadingGame, setLoadingGame] = useState(false);

  // State for ISK/Hour parser
  const [iskSellPrice, setIskSellPrice] = useState("");
  const [iskMakeCost, setIskMakeCost] = useState("");
  const [iskData, setIskData] = useState("");
  const [loadingIsk, setLoadingIsk] = useState(false);

  // Show invention fields if T2
  const showInvention = tier === "T2";

  // Handle From Game form submit
  const handleGameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingGame(true);

    try {
      const lines = blueprintData.split("\n");
      const blueprintName = lines[0]?.split("\t")[0].replace(" Blueprint", "") || "Unknown Blueprint";
      let chance = inventionChance ? parseFloat(inventionChance) / 100 : null;

      // If T2 and chance is missing, default to 1 (100%)
      if (tier === "T2" && (!chance || isNaN(chance))) {
        chance = 1;
        setInventionChance("100");
      }

      const payload = {
        name: blueprintName,
        materials: blueprintData,
        invention_materials: inventionData,
        sell_price: parseFloat(sellPrice) || 0,
        material_cost: parseFloat(makeCost) || 0,
        invention_chance: chance,
        tier,
        runs_per_copy: runsPerCopy,
        station_id: stationId ? parseInt(stationId) : null,
      };

      const res = await fetch("/api/blueprints/blueprint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        toast.success("Blueprint added successfully!");
        setSellPrice("");
        setMakeCost("");
        setBlueprintData("");
        setInventionData("");
        setInventionChance("");
        setRunsPerCopy("10");
        setStationId("");
        // Optionally: reload blueprints list
      } else {
        const err = await res.json();
        toast.error("Error adding blueprint: " + (err.error || "Unknown error"));
      }
    } catch (err: any) {
      toast.error("Error adding blueprint: " + (err.message || "Unknown error"));
    } finally {
      setLoadingGame(false);
    }
  };

  // Handle ISK/Hour form submit
  const handleIskSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingIsk(true);

    try {
      const lines = iskData.split("\n");
      const nameMatch = lines[0]?.match(/['"]?([^'"]+) Blueprint['"]?/i);
      const blueprintName = nameMatch ? nameMatch[1] : "Unknown Blueprint";

      const payload = {
        name: blueprintName,
        materials: iskData,
        sell_price: parseFloat(iskSellPrice) || 0,
        material_cost: parseFloat(iskMakeCost) || 0,
      };

      const res = await fetch("/api/blueprints/blueprint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.ok) {
        toast.success(data.message || "Blueprint added successfully!");
        setIskSellPrice("");
        setIskMakeCost("");
        setIskData("");
        if (data.dependencies_needed && data.dependencies_needed.length > 0) {
          toast.info(
            "You need to manufacture the following components:\n" +
              data.dependencies_needed.join("\n")
          );
        }
        // Optionally: reload blueprints list
      } else {
        toast.error("Error adding blueprint: " + (data.error || "Unknown error"));
      }
    } catch (err: any) {
      toast.error("Error adding blueprint: " + (err.message || "Unknown error"));
    } finally {
      setLoadingIsk(false);
    }
  };

  return (
    <section className="w-full flex flex-col items-center py-8">
      <h2 className="text-2xl font-bold mb-8 text-blue-200">Add Blueprint (Copy/Paste)</h2>
      <div className="flex flex-col md:flex-row gap-8 w-full max-w-5xl">
        {/* From Game Parser */}
        <Card className="flex-1 min-w-[320px] bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-xl rounded-2xl">
          <CardHeader>
            <CardTitle className="text-blue-100">From Game</CardTitle>
          </CardHeader>
          <form onSubmit={handleGameSubmit}>
            <CardContent className="flex flex-col gap-4">
              <div>
                <Label htmlFor="blueprintParseTier" className="text-blue-200">Blueprint Tier</Label>
                <Select value={tier} onValueChange={value => setTier(value as BlueprintTier)}>
                  <SelectTrigger id="blueprintParseTier" className="mt-1 bg-slate-800 text-blue-100 border-blue-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="T1">T1</SelectItem>
                    <SelectItem value="T2">T2</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-4">
                <Input
                  type="number"
                  id="blueprintParseSellPrice"
                  placeholder="Sell Price"
                  value={sellPrice}
                  onChange={e => setSellPrice(e.target.value)}
                  required
                  className="bg-slate-800 text-blue-100 border-blue-700"
                />
                <Input
                  type="number"
                  id="blueprintParseMakeCost"
                  placeholder="Make Cost (0 = est. cost)"
                  value={makeCost}
                  onChange={e => setMakeCost(e.target.value)}
                  className="bg-slate-800 text-blue-100 border-blue-700"
                />
              </div>
              <div className="flex flex-col md:flex-row gap-4">
                <Textarea
                  id="blueprintParseData"
                  placeholder="Paste blueprint data here"
                  value={blueprintData}
                  onChange={(e: { target: { value: SetStateAction<string>; }; }) => setBlueprintData(e.target.value)}
                  required
                  className="flex-1 min-h-[180px] bg-slate-800 text-blue-100 border-blue-700 resize-y"
                />
                {showInvention && (
                  <div className="flex-1 flex flex-col gap-2">
                    <Textarea
                      id="blueprintParseInventionData"
                      placeholder="Paste invention data here"
                      value={inventionData}
                      onChange={(e: { target: { value: SetStateAction<string>; }; }) => setInventionData(e.target.value)}
                      className="min-h-[120px] bg-slate-800 text-blue-100 border-blue-700 resize-y"
                    />
                    <Input
                      type="number"
                      id="blueprintParseInventionChance"
                      placeholder="Invention chance (%)"
                      min="0"
                      max="100"
                      step="0.01"
                      value={inventionChance}
                      onChange={e => setInventionChance(e.target.value)}
                      className="bg-slate-800 text-blue-100 border-blue-700"
                    />
                    <Label htmlFor="blueprintParseRunsPerCopy" className="text-blue-200">
                      Runs per Invented Copy
                    </Label>
                    <Select value={runsPerCopy} onValueChange={setRunsPerCopy}>
                      <SelectTrigger id="blueprintParseRunsPerCopy" className="bg-slate-800 text-blue-100 border-blue-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="10">10 Runs</SelectItem>
                        <SelectItem value="1">1 Run</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
              <div>
                <Label htmlFor="blueprintParseStation" className="text-blue-200">Manufacturing Station</Label>
                <Select value={stationId} onValueChange={setStationId}>
                  <SelectTrigger id="blueprintParseStation" className="mt-1 bg-slate-800 text-blue-100 border-blue-700">
                    <SelectValue placeholder="None (Use Jita)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Jita">None (Use Jita)</SelectItem>
                    {stations.map((s) => (
                      <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
            <CardFooter>
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-blue-700 via-blue-900 to-blue-800 text-white font-bold"
                disabled={loadingGame}
              >
                {loadingGame ? "Adding..." : "Add Blueprint"}
              </Button>
            </CardFooter>
          </form>
        </Card>

        {/* ISK/Hour Parser */}
        <Card className="flex-1 min-w-[320px] bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 border-blue-800 shadow-xl rounded-2xl">
          <CardHeader>
            <CardTitle className="text-blue-100">From ISK/Hour</CardTitle>
          </CardHeader>
          <form onSubmit={handleIskSubmit}>
            <CardContent className="flex flex-col gap-4">
              <div className="flex gap-4">
                <Input
                  type="number"
                  id="iskHourSellPrice"
                  placeholder="Sell Price"
                  value={iskSellPrice}
                  onChange={e => setIskSellPrice(e.target.value)}
                  required
                  className="bg-slate-800 text-blue-100 border-blue-700"
                />
                <Input
                  type="number"
                  id="iskHourMakeCost"
                  placeholder="Make Cost (0 = est. cost)"
                  value={iskMakeCost}
                  onChange={e => setIskMakeCost(e.target.value)}
                  className="bg-slate-800 text-blue-100 border-blue-700"
                />
              </div>
              <Textarea
                id="iskHourParseData"
                placeholder="Paste ISK/Hour material list here"
                value={iskData}
                onChange={(e: { target: { value: SetStateAction<string>; }; }) => setIskData(e.target.value)}
                required
                className="min-h-[180px] bg-slate-800 text-blue-100 border-blue-700 resize-y"
              />
            </CardContent>
            <CardFooter>
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-blue-700 via-blue-900 to-blue-800 text-white font-bold"
                disabled={loadingIsk}
              >
                {loadingIsk ? "Adding..." : "Add Blueprint"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </section>
  );
}
