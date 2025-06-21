import { Toaster } from "sonner";
import LoginPanel from "@/components/auth/LoginPanel";
import Stations from "@/components/stations/Stations";
import { mockBlueprints } from "@/types/blueprints";
import BlueprintsPage from "@/components/blueprints/Blueprints";
import Materials from "@/components/materials/Materials";
import Optimize from "@/components/optimize/Optimize";

export default function Home() {
  return (
    <> 
    <Toaster
      position="top-right"
      theme="light"
      toastOptions={{
        className: "bg-blue-100 text-blue-900 border border-blue-300 shadow-lg",
        style: {
          backgroundColor: "#dbeafe", 
          color: "#1e3a8a",
          borderColor: "#93c5fd",
        },
      }}
    />
      <LoginPanel />

      {/* Grid for Stations and Materials */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 px-8 py-10 max-w-7xl mx-auto items-stretch">
        <div className="h-full">
          <Stations />
        </div>
        <div className="h-full">
          <Materials />
        </div>
      </div>
      {/* Full-width Blueprints section */}
      <div className="px-8 max-w-7xl mx-auto pb-10">
        <BlueprintsPage />
      </div>

      <div className="px-8 max-w-7xl mx-auto pb-10">
        <Optimize />
      </div>
    </>
  );
}