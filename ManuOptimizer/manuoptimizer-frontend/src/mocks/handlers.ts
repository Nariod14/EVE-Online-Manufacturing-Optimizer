import { http, HttpResponse } from 'msw';
import { S } from 'vitest/dist/chunks/config.d.D2ROskhv.js';
import { mockBlueprints } from '@/types/blueprints';
import { Material, mockMaterials } from '@/types/materials';
import { mockStations } from '@/types/stations';
import { mock } from 'node:test';

let localStations = [...mockStations];
let localMaterials = [...mockMaterials];
export const handlers = [
  // GET /api/stations
  http.get('/api/stations', () => {
    console.log("🛰️ MSW Intercepted /api/stations");
    return HttpResponse.json(localStations);
  }),
  // POST /api/stations
  http.post('/api/stations', async ({
    request
  }) => {
    const body = await request.json() as {
      name: string;
      station_id: number;
    };
    const newStation = {
      id: Date.now(),
      ...body,
      blueprints: []
    };
    localStations.push(newStation);
    return HttpResponse.json(newStation, {
      status: 201
    });
  }),
  // PUT /api/stations/:id
  http.put('/api/stations/:id', async ({
    params,
    request
  }) => {
    const {
      id
    } = params;
    const body = await request.json() as {
      name: string;
      station_id: number;
    };
    localStations = localStations.map(s => s.id === Number(id) ? {
      ...s,
      ...body
    } : s);
    return HttpResponse.json({
      success: true
    });
  }),
  // DELETE /api/stations/:id
  http.delete('/api/stations/:id', ({
    params
  }) => {
    const {
      id
    } = params;
    localStations = localStations.filter(s => s.id !== Number(id));
    return HttpResponse.json({
      success: true
    });
  }),
  // GET blueprints
  http.get('/api/blueprints/blueprints', ({
    request
  }) => {
    console.log("Registered handlers:", handlers.map(h => h.info?.path));
    console.log('[MSW] Intercepted request:', request.url)
    console.log("[MSW] mockBlueprints:", mockBlueprints);
    return HttpResponse.json(mockBlueprints)
  }),
  // DELETE blueprint
  http.delete("/api/blueprints/blueprint/:id", ({
    params
  }) => {
    const {
      id
    } = params
    console.log(`Mock delete blueprint ${id}`)
    return HttpResponse.json({
      success: true
    })
  }),
  // PUT update max or reset
  http.put("/api/blueprints/blueprint/:id", async ({
    request,
    params
  }) => {
    const body = await request.json()
    console.log(`Mock update blueprint ${params.id} with body:`, body)
    return HttpResponse.json({
      success: true
    })
  }),
  // POST reset all max values
  http.post("/api/blueprints/blueprints/reset_max", () => {
    console.log(`Mock reset all blueprint max values`)
    return HttpResponse.json({
      success: true
    })
  }),

  http.get('/api/materials/materials', () => {
    console.log("🛰️ MSW Intercepted /api/materials/materials");
    return HttpResponse.json(localMaterials);
  }),

  // GET single material by ID
  http.get("/api/materials/material/:id", ({ params }) => {
    const id = Number(params.id);
    const material = localMaterials.find((m) => m.id === id);

    if (!material) {
      return new HttpResponse("Material not found", { status: 404 });
    }

    return HttpResponse.json(material);
  }),

  // POST update material info (simulated)
  http.put("/api/materials/material/:id", async ({ request, params }) => {
    const id = Number(params.id);
    const updatedMaterial = await request.json() as Partial<Material>;

    const index = localMaterials.findIndex((mat) => mat.id === id);
    if (index === -1) {
      console.warn(`🛰️ Material with id ${id} not found for update`);
      return new HttpResponse("Material not found", { status: 404 });
    }

    localMaterials = localMaterials.map((mat) =>
      mat.id === id ? { ...mat, ...updatedMaterial, id } : mat
    );

    console.log(`🛰️ Updated Material ${id}:`, localMaterials[index]);
    return HttpResponse.json(localMaterials[index]);
  }),

  // DELETE material
  http.delete("/api/materials/material/:id", ({ params }) => {
    const id = Number(params.id);
    const index = localMaterials.findIndex((m) => m.id === id);
    if (index === -1) {
      return new HttpResponse("Material not found", { status: 404 });
    }

    const deleted = localMaterials.splice(index, 1)[0];
    console.log(`🛰️ MSW Deleted Material ${id}`);
    return HttpResponse.json(deleted);
  }),

  // POST to add a new material
  http.post("/api/materials/material", async ({ request }) => {
    const newMaterial = await request.json() as Material;

    const newId = localMaterials.length > 0 ? Math.max(...localMaterials.map((m) => m.id)) + 1 : 1;
    const created = { ...newMaterial, id: newId };

    localMaterials.push(created);

    console.log(`🛰️ MSW Created Material ${newId}:`, created);
    return HttpResponse.json(created);
  }),

];
