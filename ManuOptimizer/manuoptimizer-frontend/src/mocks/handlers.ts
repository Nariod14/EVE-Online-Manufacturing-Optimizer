import { http, HttpResponse } from 'msw';
import { S } from 'vitest/dist/chunks/config.d.D2ROskhv.js';
import { mockBlueprints } from '@/types/blueprints';
import { mockMaterials } from '@/types/materials';
import { mockStations } from '@/types/stations';
import { mock } from 'node:test';

let localStations = [...mockStations];
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
  })
];
