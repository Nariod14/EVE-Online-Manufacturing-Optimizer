

export type Material = {
    id: number;
    sell_price?: number | null;
    name: string;
    quantity: number;
    type_id?: number | null;
    category?: string | null;
};


export const mockMaterials: Material[] = [
{
    id: 1,
    sell_price: 1000,
    name: "Tritanium",
    quantity: 100,
    type_id: 34,
    category: "Minerals"
},
{
    id: 2,
    sell_price: 500,
    name: "Pyerite",
    quantity: 50,
    type_id: 35,
    category: "Minerals"
},
{
    id: 3,
    sell_price: 2000,
    name: "Mexallon",
    quantity: 20,
    type_id: 36,
    category: "Minerals"
},
{
    id: 4,
    sell_price: 10000,
    name: "Drone Structure",
    quantity: 10,
    type_id: 1234,
    category: "Components"
},
{
    id: 5,
    sell_price: 5000,
    name: "Morphite",
    quantity: 5,
    type_id: 5678,
    category: "Components"
},
{
    id: 6,
    sell_price: 20000,
    name: "Advanced Drone Structure",
    quantity: 2,
    type_id: 9012,
    category: "T2 Components"
}
];
