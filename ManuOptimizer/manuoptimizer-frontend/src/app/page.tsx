import Image from "next/image";
import LoginPanel from "@/components/auth/LoginPanel";
import Stations from "@/components/stations/Stations";
import StationListTest from "@/components/stationsTests/StationListTest";
import BlueprintParserTest from "@/components/blueprintsTests/BluerintParserTest";
import BlueprintListTest from "@/components/blueprintsTests/BlueprintListTest";
import { mockBlueprints } from "@/types/blueprints";
import BlueprintsPage from "@/components/blueprints/Bluepritns";
import BlueprintParser from "@/components/blueprints/BlueprintParsers";

export default function Home() {
  return (
    <>
      <LoginPanel />
      <Stations />
      <BlueprintParser />
      {/* <BlueprintListTest blueprints={mockBlueprints}/> */}
      <BlueprintsPage />
    </>
  );
}