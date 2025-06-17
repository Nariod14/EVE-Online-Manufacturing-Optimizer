import { Toaster } from "sonner";
import LoginPanel from "@/components/auth/LoginPanel";
import Stations from "@/components/stations/Stations";
import { mockBlueprints } from "@/types/blueprints";
import BlueprintsPage from "@/components/blueprints/Bluepritns";
import Materials from "@/components/materials/Materials";

export default function Home() {
  return (
    <> 
    <Toaster
      position="top-right"
      theme="light" // switch from "dark" to "light"
      toastOptions={{
        className: "bg-blue-100 text-blue-900 border border-blue-300 shadow-lg",
        style: {
          backgroundColor: "#dbeafe", // Tailwind bg-blue-50
          color: "#1e3a8a", // Tailwind blue-900
          borderColor: "#93c5fd", // Tailwind blue-300
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
    </>
  );
}