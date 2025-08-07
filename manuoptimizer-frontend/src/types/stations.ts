import { waitForMswReady } from "@/lib/mswReady";


export const mockStations = [
  {
    id: 1,
    name: "Amarr VIII (Oris) - Emperor Family Academy",
    station_id: 60003760,
  },
  {
    id: 2,
    name: "Jita IV - Moon 4 - Caldari Navy Assembly Plant",
    station_id: 60011866,
  },
  {
    id: 3,
    name: "Rens VI - Moon 8 - Brutor Tribe Treasury",
    station_id: 60004588,
  },
  {
    id: 4,
    name: "Dodixie IX - Moon 20 - Federation Navy Assembly Plant",
    station_id: 60005686,
  },
];


export type Station = {
    id: number;
    name: string;
    station_id: number;// Optional
  };


  export const fetchStations = async (): Promise<Station[]> => {
    if (process.env.NODE_ENV === 'development') {
      await waitForMswReady(); // only in dev
    }

    console.log("MSW ready. Requesting /api/stations");

    try {
      const res = await fetch("/api/stations");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data;
    } catch (err: any) {
      console.error("Failed to fetch stations:", err);
      return []; // Return an empty array on error
    }
  }