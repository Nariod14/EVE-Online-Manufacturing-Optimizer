"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

type BlueprintTier = "T1" | "T2";

type Blueprint = {
  id: number;
  type_id?: number | null;
  name: string;
  materials: any;
  sell_price: number;
  max?: number | null;
  material_cost: number;
  tier: BlueprintTier;
  station_id?: number | null;
  region_id: number;
  use_jita_sell: boolean;
  used_jita_fallback: boolean;
};

const MOCK_STATIONS = [
  { id: 60003760, name: "Jita IV - Moon 4" },
  { id: 60008494, name: "Amarr VIII (Oris)" },
  { id: 60011866, name: "Dodixie IX - Moon 20" },
  { id: 60004588, name: "Rens VI - Moon 8" },
];

export default function BlueprintParserTest() {
  // Local blueprint state
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
  const [nextId, setNextId] = useState(1);

  // Form states (From Game)
  const [tier, setTier] = useState<BlueprintTier>("T1");
  const [sellPrice, setSellPrice] = useState("");
  const [makeCost, setMakeCost] = useState("");
  const [blueprintData, setBlueprintData] = useState("");
  const [inventionData, setInventionData] = useState("");
  const [inventionChance, setInventionChance] = useState("");
  const [runsPerCopy, setRunsPerCopy] = useState("10");
  const [stationId, setStationId] = useState("");
  const [loadingGame, setLoadingGame] = useState(false);

  // Form states (ISK/Hour)
  const [iskSellPrice, setIskSellPrice] = useState("");
  const [iskMakeCost, setIskMakeCost] = useState("");
  const [iskData, setIskData] = useState("");
  const [loadingIsk, setLoadingIsk] = useState(false);

  // Show invention fields if T2
  const showInvention = tier === "T2";

  // Handle From Game form submit
  const handleGameSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingGame(true);

    try {
      const lines = blueprintData.split("\n");
      const blueprintName = lines[0]?.split("\t")[0].replace(" Blueprint", "") || "Unknown Blueprint";
      let chance = inventionChance ? parseFloat(inventionChance) / 100 : null;

      if (tier === "T2" && (!chance || isNaN(chance))) {
        chance = 1;
        setInventionChance("100");
      }

      const newBlueprint: Blueprint = {
        id: nextId,
        name: blueprintName,
        materials: blueprintData,
        sell_price: parseFloat(sellPrice) || 0,
        material_cost: parseFloat(makeCost) || 0,
        tier,
        station_id: stationId ? parseInt(stationId) : null,
        region_id: 10000002,
        use_jita_sell: !stationId,
        used_jita_fallback: false,
        type_id: null,
        max: null,
      };

      setBlueprints((prev) => [...prev, newBlueprint]);
      setNextId((id) => id + 1);

      toast.success("Blueprint added locally!");
      setSellPrice("");
      setMakeCost("");
      setBlueprintData("");
      setInventionData("");
      setInventionChance("");
      setRunsPerCopy("10");
      setStationId("");
    } catch (err: any) {
      toast.error("Error adding blueprint: " + (err.message || "Unknown error"));
    } finally {
      setLoadingGame(false);
    }
  };

  // Handle ISK/Hour form submit
  const handleIskSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingIsk(true);

    try {
      const lines = iskData.split("\n");
      const nameMatch = lines[0]?.match(/['"]?([^'"]+) Blueprint['"]?/i);
      const blueprintName = nameMatch ? nameMatch[1] : "Unknown Blueprint";

      const newBlueprint: Blueprint = {
        id: nextId,
        name: blueprintName,
        materials: iskData,
        sell_price: parseFloat(iskSellPrice) || 0,
        material_cost: parseFloat(iskMakeCost) || 0,
        tier: "T1",
        station_id: null,
        region_id: 10000002,
        use_jita_sell: true,
        used_jita_fallback: false,
        type_id: null,
        max: null,
      };

      setBlueprints((prev) => [...prev, newBlueprint]);
      setNextId((id) => id + 1);

      toast.success("Blueprint added locally!");
      setIskSellPrice("");
      setIskMakeCost("");
      setIskData("");
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
                  onChange={e => setBlueprintData(e.target.value)}
                  required
                  className="flex-1 min-h-[180px] bg-slate-800 text-blue-100 border-blue-700 resize-y"
                />
                {showInvention && (
                  <div className="flex-1 flex flex-col gap-2">
                    <Textarea
                      id="blueprintParseInventionData"
                      placeholder="Paste invention data here"
                      value={inventionData}
                      onChange={e => setInventionData(e.target.value)}
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
                    {MOCK_STATIONS.map((s) => (
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
                onChange={e => setIskData(e.target.value)}
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

      {/* Blueprint List */}
      <div className="w-full max-w-5xl mt-12">
        <h3 className="text-xl font-bold mb-4 text-blue-200">Local Blueprints</h3>
        {blueprints.length === 0 ? (
          <div className="text-blue-400">No blueprints added yet.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {blueprints.map((bp) => (
              <Card key={bp.id} className="rounded-xl bg-slate-900/80 border-blue-800">
                <CardHeader>
                  <CardTitle className="text-blue-100">{bp.name}</CardTitle>
                </CardHeader>
                <CardContent className="text-blue-200 space-y-1">
                  <div>
                    <span className="font-semibold">Tier:</span> {bp.tier}
                  </div>
                  <div>
                    <span className="font-semibold">Sell Price:</span> {bp.sell_price.toLocaleString()}
                  </div>
                  <div>
                    <span className="font-semibold">Material Cost:</span> {bp.material_cost.toLocaleString()}
                  </div>
                  <div>
                    <span className="font-semibold">Station:</span>{" "}
                    {MOCK_STATIONS.find(s => s.id === bp.station_id)?.name || "Jita"}
                  </div>
                  <div>
                    <span className="font-semibold">Materials:</span>
                    <pre className="whitespace-pre-wrap text-xs bg-slate-800 rounded p-2 mt-1">{typeof bp.materials === "string" ? bp.materials : JSON.stringify(bp.materials, null, 2)}</pre>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
