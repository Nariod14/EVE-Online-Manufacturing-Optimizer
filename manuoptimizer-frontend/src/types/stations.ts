

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